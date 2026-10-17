// Post-analysis export of everything except decompiler output.
// Args: <out-dir>
// Writes: functions.tsv, callgraph.tsv, symbols.tsv, strings.tsv, types.h, disasm.jsonl
//@category T7
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.Writer;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import com.google.gson.JsonObject;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressRange;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.data.DataTypeManager;
import ghidra.program.model.data.DataTypeWriter;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.RefType;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.symbol.SymbolType;

public class ExportAll extends GhidraScript {

	static String clean(String s) {
		return s == null ? "" : s.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ');
	}

	static String hex(Address a) {
		return String.format("%09X", a.getOffset());
	}

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		File out = new File(args[0]);
		out.mkdirs();
		Listing listing = currentProgram.getListing();
		Memory mem = currentProgram.getMemory();

		// functions.tsv + disasm.jsonl + callgraph.tsv in one pass
		try (Writer fw = new BufferedWriter(new FileWriter(new File(out, "functions.tsv")));
				Writer cw = new BufferedWriter(new FileWriter(new File(out, "callgraph.tsv")));
				Writer dw = new BufferedWriter(new FileWriter(new File(out, "disasm.jsonl")))) {
			fw.write("va\tsize\tname\tnamespace\tsignature\tcalling_convention\tthunk\tname_source\tinstructions\tbytes_sha256\n");
			cw.write("caller\tcallee\tkind\tsite\n");
			FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
			int n = 0;
			while (it.hasNext()) {
				monitor.checkCancelled();
				Function f = it.next();
				if (f.isExternal()) {
					continue;
				}
				AddressSetView body = f.getBody();
				MessageDigest md = MessageDigest.getInstance("SHA-256");
				for (AddressRange r : body) {
					byte[] b = new byte[(int) r.getLength()];
					mem.getBytes(r.getMinAddress(), b);
					md.update(b);
				}
				StringBuilder sb = new StringBuilder();
				for (byte x : md.digest()) {
					sb.append(String.format("%02x", x));
				}
				StringBuilder asm = new StringBuilder();
				Set<String> seen = new HashSet<>();
				int insns = 0;
				InstructionIterator ii = listing.getInstructions(body, true);
				while (ii.hasNext()) {
					Instruction ins = ii.next();
					insns++;
					Symbol lbl = currentProgram.getSymbolTable().getPrimarySymbol(ins.getAddress());
					if (lbl != null && !ins.getAddress().equals(f.getEntryPoint())) {
						asm.append(lbl.getName()).append(":\n");
					}
					StringBuilder bytes = new StringBuilder();
					for (byte x : ins.getBytes()) {
						bytes.append(String.format("%02X", x));
					}
					asm.append(String.format("  %s  %-20s %s%n", hex(ins.getAddress()), bytes, ins));
					for (Reference ref : ins.getReferencesFrom()) {
						RefType rt = ref.getReferenceType();
						if (!rt.isCall() && !rt.isJump()) {
							continue;
						}
						Function callee = getFunctionAt(ref.getToAddress());
						if (callee == null || (rt.isJump() && callee.equals(f))) {
							continue;
						}
						String kind = rt.isCall() ? "call" : "tailcall";
						String key = hex(callee.getEntryPoint()) + kind + hex(ins.getAddress());
						if (seen.add(key)) {
							cw.write(hex(f.getEntryPoint()) + "\t" + hex(callee.getEntryPoint()) + "\t" + kind + "\t"
									+ hex(ins.getAddress()) + "\n");
						}
					}
				}
				Function thunked = f.isThunk() ? f.getThunkedFunction(false) : null;
				fw.write(String.join("\t", hex(f.getEntryPoint()), Long.toString(body.getNumAddresses()),
						clean(f.getName()), clean(f.getParentNamespace().getName(true)),
						clean(f.getPrototypeString(false, false)), clean(f.getCallingConventionName()),
						thunked == null ? "" : clean(thunked.getName(true)),
						f.getSymbol().getSource().toString(), Integer.toString(insns), sb.toString()) + "\n");
				JsonObject o = new JsonObject();
				o.addProperty("va", hex(f.getEntryPoint()));
				o.addProperty("name", f.getName(true));
				o.addProperty("asm", asm.toString());
				dw.write(o.toString() + "\n");
				if (++n % 5000 == 0) {
					println("exported " + n + " functions");
				}
			}
			println("functions: " + n);
		}

		// symbols.tsv: every non-function symbol in loaded memory
		try (Writer sw = new BufferedWriter(new FileWriter(new File(out, "symbols.tsv")))) {
			sw.write("va\tname\tnamespace\ttype\tsource\tblock\tdatatype\tlength\n");
			SymbolIterator si = currentProgram.getSymbolTable().getAllSymbols(true);
			while (si.hasNext()) {
				Symbol s = si.next();
				if (s.isExternal() || s.getSymbolType() == SymbolType.FUNCTION) {
					continue;
				}
				Address a = s.getAddress();
				if (!a.isMemoryAddress() || getFunctionContaining(a) != null) {
					continue;
				}
				MemoryBlock blk = mem.getBlock(a);
				Data d = listing.getDataAt(a);
				sw.write(String.join("\t", hex(a), clean(s.getName()), clean(s.getParentNamespace().getName(true)),
						s.getSymbolType().toString(), s.getSource().toString(), blk == null ? "" : blk.getName(),
						d == null ? "" : clean(d.getDataType().getPathName()),
						d == null ? "" : Integer.toString(d.getLength())) + "\n");
			}
		}

		// strings.tsv
		try (Writer tw = new BufferedWriter(new FileWriter(new File(out, "strings.tsv")))) {
			tw.write("va\ttype\tvalue\n");
			for (Data d : listing.getDefinedData(true)) {
				if (!d.hasStringValue()) {
					continue;
				}
				Object v = d.getValue();
				tw.write(hex(d.getAddress()) + "\t" + clean(d.getDataType().getName()) + "\t"
						+ clean(v == null ? "" : v.toString().replace("\\", "\\\\")) + "\n");
			}
		}

		// types.h: every data type the PDB + analysis produced, as C
		DataTypeManager dtm = currentProgram.getDataTypeManager();
		try (Writer hw = new BufferedWriter(new FileWriter(new File(out, "types.h")))) {
			new DataTypeWriter(dtm, hw).write(dtm, monitor);
		}
	}
}
