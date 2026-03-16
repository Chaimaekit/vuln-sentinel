import requests
import json
import config
import threading


_llm_lock = threading.Lock()



def analyze_with_llm(findings, filename, mode="deep"):

    with _llm_lock:
        model     = config.MODELS[mode]
        file_type = findings.get("type", "unknown")

        print(f"  [*] Sending to LLM ({model})...")

        if file_type == "binary":
            basic     = findings.get("basic_checks", {})
            context   = "\n".join([
                "dangerous:" + basic.get("dangerous_functions", "none")[:200],
                "strings:"   + basic.get("interesting_strings",  "none")[:150],
                "checksec:"  + basic.get("checksec",              "none")[:100],
                "code:"      + findings.get("decompiled_snippet", "none")[:400],
            ])
        else:
            context = "semgrep:" + json.dumps(
                findings.get("semgrep_findings", [])[:3]
            )[:300]

        prompt = (
            f'You are a security analyst. Analyze "{filename}".\n'
            f'Evidence:\n{context}\n\n'
            f'Reply ONLY with this JSON and nothing else:\n'
            f'{{"risk_score":8,"confidence":7,"risk_level":"high",'
            f'"verdict":"one sentence here",'
            f'"confirmed_vulnerabilities":[{{"type":"buffer overflow",'
            f'"location":"vulnerable_input","severity":"high",'
            f'"explanation":"explain here","exploitable":true}}],'
            f'"recommended_actions":["action here"],'
            f'"summary":"two sentences here"}}'
        )

        default = {
            "risk_score":                0,
            "confidence":                0,
            "risk_level":                "unknown",
            "verdict":                   "LLM analysis failed",
            "confirmed_vulnerabilities": [],
            "recommended_actions":       ["Manual review required"],
            "summary":                   "LLM analysis failed. Manual review needed."
        }

        try:
            response = requests.post(
                config.OLLAMA_URL,
                json={
                    "model":  model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=400
            )

            raw   = response.json().get("response", "")
            clean = raw.replace("```json", "").replace("```", "").strip()

            start = clean.find("{")
            end   = clean.rfind("}") + 1
            if start == -1 or end <= start:
                print(f"  [!] No JSON found in LLM response")
                return default

            result = json.loads(clean[start:end])

            raw_score = result.get("risk_score", 0)
            try:
                result["risk_score"] = int(raw_score)
            except (ValueError, TypeError):
                level_map = {
                    "low": 3, "medium": 5,
                    "high": 8, "critical": 10
                }
                result["risk_score"] = level_map.get(
                    str(raw_score).lower(), 0
                )

            print(
                f"  [*] LLM risk score: {result.get('risk_score')}/10 "
                f"(confidence: {result.get('confidence')}/10)"
            )
            return result

        except json.JSONDecodeError as e:
            print(f"  [!] LLM JSON parse error: {e}")
        except requests.exceptions.Timeout:
            print(f"  [!] LLM timed out")
        except Exception as e:
            print(f"  [!] LLM error: {e}")

        return default
