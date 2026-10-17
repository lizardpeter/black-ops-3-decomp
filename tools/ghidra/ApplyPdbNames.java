// Apply the PDB's parameter and local-variable names (and local types) to analysed functions.
// Ghidra's PDB analyzer applies function signatures and types but leaves variables as param_N/local_N.
// Args: <analysis/<build>/pdb/locals.tsv>   (written by tools/pdb/extract.py; offsets are Ghidra stack offsets)
//@category T7
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.data.DataType;
import ghidra.program.model.data.DataTypeManager;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.LocalVariableImpl;
import ghidra.program.model.listing.Variable;
import ghidra.program.model.symbol.SourceType;
import ghidra.util.data.DataTypeParser;
import ghidra.util.data.DataTypeParser.AllowedDataTypes;

public class ApplyPdbNames extends GhidraScript {

	private DataTypeParser parser;

	private DataType parse(String ty) {
		if (ty.isEmpty()) {
			return null;
		}
		String t = ty.replace("const ", "").replace("volatile ", "").replace("*", " *").trim();
		try {
			return parser.parse(t);
		}
		catch (Exception e) {
			return null;
		}
	}

	private static Variable findStack(Function f, int off, boolean param) {
		Variable[] vars = param ? f.getParameters() : f.getLocalVariables();
		for (Variable v : vars) {
			if (v.isStackVariable() && v.getStackOffset() == off) {
				return v;
			}
		}
		return null;
	}

	@Override
	public void run() throws Exception {
		File tsv = new File(getScriptArgs()[0]);
		Map<String, List<String[]>> byVa = new LinkedHashMap<>();
		try (BufferedReader r = new BufferedReader(new FileReader(tsv))) {
			String line = r.readLine(); // header
			while ((line = r.readLine()) != null) {
				String[] c = line.split("\t", -1);
				byVa.computeIfAbsent(c[0], k -> new ArrayList<>()).add(c);
			}
		}
		DataTypeManager dtm = currentProgram.getDataTypeManager();
		parser = new DataTypeParser(dtm, dtm, null, AllowedDataTypes.ALL);

		int funcs = 0, noFunc = 0, renamed = 0, created = 0, typed = 0, skipped = 0;
		for (Map.Entry<String, List<String[]>> e : byVa.entrySet()) {
			monitor.checkCancelled();
			Function f = getFunctionAt(toAddr(Long.parseLong(e.getKey(), 16)));
			if (f == null) {
				noFunc++;
				continue;
			}
			funcs++;
			Set<String> used = new HashSet<>();
			for (String[] c : e.getValue()) {
				boolean param = c[1].equals("param");
				int off = Integer.parseInt(c[2]);
				String name = c[3];
				for (int n = 2; !used.add(name); n++) {
					name = c[3] + "_" + n;
				}
				DataType dt = param ? null : parse(c[4]);
				try {
					Variable v = findStack(f, off, param);
					if (v == null) {
						if (param || dt == null) {
							skipped++;
							continue;
						}
						f.addLocalVariable(new LocalVariableImpl(name, dt, off, currentProgram), SourceType.IMPORTED);
						created++;
						continue;
					}
					v.setName(name, SourceType.IMPORTED);
					renamed++;
					if (dt != null && dt.getLength() > 0 && dt.getLength() <= v.getLength()) {
						v.setDataType(dt, SourceType.IMPORTED);
						typed++;
					}
				}
				catch (Exception ex) {
					skipped++;
				}
			}
		}
		println(String.format("PDB names: %d functions (%d not found), %d renamed, %d locals created, %d locals typed, %d skipped",
			funcs, noFunc, renamed, created, typed, skipped));
	}
}
