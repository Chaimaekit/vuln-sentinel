// ExportDecompiled.java
// Ghidra script that exports decompiled C code for all functions
//@category VulnSentinel

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.util.task.ConsoleTaskMonitor;
import java.io.FileWriter;
import java.io.File;

public class ExportDecompiled extends GhidraScript {

    @Override
    public void run() throws Exception {
        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);

        String outputPath = System.getProperty("java.io.tmpdir") +
            "/ghidra_out_" + currentProgram.getName() + "/" +
            currentProgram.getName() + "_decompiled.c";

        // Create output directory
        new File(outputPath).getParentFile().mkdirs();

        FileWriter writer = new FileWriter(outputPath);
        FunctionManager fm = currentProgram.getFunctionManager();

        writer.write("// Decompiled by VulnSentinel + Ghidra\n");
        writer.write("// File: " + currentProgram.getName() + "\n\n");

        // Decompile every function
        for (Function func : fm.getFunctions(true)) {
            try {
                DecompileResults result = decomp.decompileFunction(
                    func, 30, new ConsoleTaskMonitor()
                );
                if (result != null && result.decompileCompleted()) {
                    writer.write("// Function: " + func.getName() + "\n");
                    writer.write(result.getDecompiledFunction().getC());
                    writer.write("\n\n");
                }
            } catch (Exception e) {
                writer.write("// Could not decompile: " + func.getName() + "\n\n");
            }
        }

        writer.close();
        decomp.dispose();
        println("Exported decompiled output to: " + outputPath);
    }
}
