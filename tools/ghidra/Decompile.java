// Decompile one shard of the program's functions to JSONL.
// Args: <out.jsonl> <shard-index> <shard-count> [timeout-seconds]
//@category T7
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.Writer;

import com.google.gson.JsonObject;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class Decompile extends GhidraScript {
	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		File out = new File(args[0]);
		int shard = Integer.parseInt(args[1]);
		int shards = Integer.parseInt(args[2]);
		int timeout = args.length > 3 ? Integer.parseInt(args[3]) : 90;

		DecompInterface ifc = new DecompInterface();
		ifc.setOptions(new DecompileOptions());
		ifc.toggleCCode(true);
		ifc.toggleSyntaxTree(false);
		ifc.setSimplificationStyle("decompile");
		if (!ifc.openProgram(currentProgram)) {
			throw new IllegalStateException("decompiler failed to open program: " + ifc.getLastMessage());
		}

		int i = 0, ok = 0, failed = 0;
		long t0 = System.currentTimeMillis();
		try (Writer w = new BufferedWriter(new FileWriter(out))) {
			FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
			while (it.hasNext()) {
				monitor.checkCancelled();
				Function f = it.next();
				if (f.isExternal() || f.isThunk() || (i++ % shards) != shard) {
					continue;
				}
				JsonObject o = new JsonObject();
				o.addProperty("va", String.format("%09X", f.getEntryPoint().getOffset()));
				o.addProperty("name", f.getName(true));
				DecompileResults r = ifc.decompileFunction(f, timeout, monitor);
				if (r != null && r.decompileCompleted() && r.getDecompiledFunction() != null) {
					o.addProperty("c", r.getDecompiledFunction().getC());
					ok++;
				}
				else {
					o.addProperty("error", r == null ? "null result" : r.getErrorMessage());
					failed++;
				}
				w.write(o.toString() + "\n");
				if ((ok + failed) % 1000 == 0) {
					println(String.format("shard %d: %d ok, %d failed, %ds", shard, ok, failed,
							(System.currentTimeMillis() - t0) / 1000));
				}
			}
		}
		ifc.dispose();
		println(String.format("shard %d done: %d ok, %d failed", shard, ok, failed));
	}
}
