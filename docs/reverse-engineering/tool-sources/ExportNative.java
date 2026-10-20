// Batch evidence export; input executable is only read by the importer.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import java.io.*;
import java.nio.charset.StandardCharsets;

public class ExportNative extends GhidraScript {
    public void run() throws Exception {
        File root = new File(getScriptArgs()[0]);
        root.mkdirs();
        File code = new File(root, "pseudocode");
        code.mkdirs();
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        int done = 0;
        try (PrintWriter inventory = new PrintWriter(new File(root, "functions.tsv"), "UTF-8");
             PrintWriter calls = new PrintWriter(new File(root, "calls.tsv"), "UTF-8")) {
            inventory.println("address\tname\tbytes\texternal\tthunk\tdecompile_status");
            calls.println("caller\tcallee");
            FunctionIterator iter = currentProgram.getFunctionManager().getFunctions(true);
            while (iter.hasNext() && !monitor.isCancelled()) {
                Function function = iter.next();
                String address = function.getEntryPoint().toString();
                for (Function target : function.getCalledFunctions(monitor)) {
                    calls.println(address + "\t" + target.getEntryPoint());
                }
                String status = "external";
                if (!function.isExternal()) {
                    DecompileResults result = decompiler.decompileFunction(function, 20, monitor);
                    status = result.decompileCompleted() ? "complete" : "failed";
                    File target = new File(code, address.replace(':', '_') + ".c");
                    try (PrintWriter output = new PrintWriter(target, "UTF-8")) {
                        output.println("/* Ghidra pseudocode, not original source. Address: " + address + " */");
                        if (result.decompileCompleted()) output.print(result.getDecompiledFunction().getC());
                        else output.println("/* " + result.getErrorMessage().replace("*/", "* /") + " */");
                    }
                }
                inventory.println(address + "\t" + function.getName() + "\t" +
                    function.getBody().getNumAddresses() + "\t" + function.isExternal() +
                    "\t" + function.isThunk() + "\t" + status);
                if (++done % 100 == 0) {
                    inventory.flush(); calls.flush(); println("EXPORTED " + done);
                }
            }
        } finally {
            decompiler.dispose();
        }
        println("EXPORT_FINISHED " + done);
    }
}
