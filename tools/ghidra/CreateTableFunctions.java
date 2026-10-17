// Post-analysis: create functions that are reached only through pointers stored in data.
//
// Ghidra's auto-analysis finds functions from calls, the entry point and .pdata, but not code that is only ever
// referenced from a table: vtables, Lua C function and console command registration tables, callback arrays.
// On BO3 that was ~5,000 functions per build (docs/builds.md), including most of the Lua and command handlers the
// community clients name. This script scans every initialized .rdata/.data block for 8-byte aligned values that
// point into an executable block, at an address no function covers yet, disassembles there and creates a
// function, then lets the analyzers process the new code. A target inside an existing function body is left
// alone (that is a pointer into the middle of known code, not a function start).
//
// Runs as a -postScript before ExportAll.java. No arguments.
//@category T7
import java.util.ArrayList;
import java.util.List;
import java.util.TreeSet;

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;

public class CreateTableFunctions extends GhidraScript {
	@Override
	public void run() throws Exception {
		Memory mem = currentProgram.getMemory();
		Listing listing = currentProgram.getListing();

		List<MemoryBlock> code = new ArrayList<>();
		List<MemoryBlock> data = new ArrayList<>();
		for (MemoryBlock b : mem.getBlocks()) {
			if (!b.isInitialized()) {
				continue;
			}
			if (b.isExecute()) {
				code.add(b);
			} else if (b.getName().startsWith(".rdata") || b.getName().startsWith(".data")) {
				data.add(b);
			}
		}

		TreeSet<Long> targets = new TreeSet<>();
		int inside = 0;
		for (MemoryBlock b : data) {
			long start = (b.getStart().getOffset() + 7) & ~7L;
			int n = (int) Math.min(b.getEnd().getOffset() + 1 - start, Integer.MAX_VALUE - 8);
			byte[] buf = new byte[n];
			mem.getBytes(toAddr(start), buf);
			for (int i = 0; i + 8 <= n; i += 8) {
				long v = 0;
				for (int k = 7; k >= 0; k--) {
					v = (v << 8) | (buf[i + k] & 0xFF);
				}
				if (!inCode(code, v)) {
					continue;
				}
				Address a = toAddr(v);
				if (getFunctionAt(a) != null) {
					continue;
				}
				if (getFunctionContaining(a) != null) {
					inside++;
					continue;
				}
				targets.add(v);
			}
		}
		println(String.format("data pointers into code with no function: %d targets (%d more point inside a function)",
			targets.size(), inside));

		int made = 0, noCode = 0, failed = 0;
		for (long v : targets) {
			monitor.checkCancelled();
			Address a = toAddr(v);
			if (getFunctionContaining(a) != null) {
				continue; // created as part of an earlier target's function
			}
			if (listing.getInstructionAt(a) == null) {
				new DisassembleCommand(a, null, true).applyTo(currentProgram, monitor);
			}
			if (listing.getInstructionAt(a) == null) {
				noCode++; // defined data there, or bytes that don't decode
				continue;
			}
			if (new CreateFunctionCmd(a).applyTo(currentProgram, monitor)) {
				made++;
			} else {
				failed++;
			}
		}
		println(String.format("created %d functions; %d targets not code, %d could not be made functions",
			made, noCode, failed));
		analyzeChanges(currentProgram);
	}

	static boolean inCode(List<MemoryBlock> code, long v) {
		for (MemoryBlock b : code) {
			if (v >= b.getStart().getOffset() && v <= b.getEnd().getOffset()) {
				return true;
			}
		}
		return false;
	}
}
