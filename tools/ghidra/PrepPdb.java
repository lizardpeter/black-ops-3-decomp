// Pre-analysis script: points Ghidra's PDB analyzer at the original PDB before auto-analysis.
// Args: <path-to-pdb>
//@category T7
import java.io.File;

import ghidra.app.plugin.core.analysis.PdbUniversalAnalyzer;
import ghidra.app.script.GhidraScript;

public class PrepPdb extends GhidraScript {
	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 1) {
			throw new IllegalArgumentException("usage: PrepPdb.java <pdb>");
		}
		File pdb = new File(args[0]);
		if (!pdb.isFile()) {
			throw new IllegalArgumentException("PDB not found: " + pdb);
		}
		PdbUniversalAnalyzer.setPdbFileOption(currentProgram, pdb);
		println("PDB set: " + pdb.getAbsolutePath());
	}
}
