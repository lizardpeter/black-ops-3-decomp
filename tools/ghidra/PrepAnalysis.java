// Pre-analysis script for every build: check the JVM heap actually available (abort below 8 GB), and run
// the analyzers that have exhausted the heap on these binaries with a single thread.
//
// On BO1 (black-ops-1-decomp) the larger builds ran out of heap inside the x86 constant-propagation analyzer
// within minutes; after that the program database is unusable for every later step.
//@category T7
import java.util.Map;

import ghidra.app.util.headless.HeadlessScript;

public class PrepAnalysis extends HeadlessScript {
	@Override
	public void run() throws Exception {
		Runtime rt = Runtime.getRuntime();
		println(String.format("JVM max heap: %d MB, processors: %d", rt.maxMemory() >> 20, rt.availableProcessors()));
		if (rt.maxMemory() < (8L << 30)) {
			// with the 2 GB default these binaries run out of heap minutes in and leave a corrupt database
			printerr("JVM heap below 8 GB: MAXMEM was not applied to analyzeHeadless; aborting");
			setHeadlessContinuationOption(HeadlessContinuationOption.ABORT_AND_DELETE);
			return;
		}

		Map<String, String> options = getCurrentAnalysisOptionsAndValues(currentProgram);
		for (Map.Entry<String, String> e : options.entrySet()) {
			String name = e.getKey();
			if (name.contains("Constant Reference Analyzer") || name.contains("Decompiler Switch Analysis")
					|| name.contains("Stack")) {
				println("option: " + name + " = " + e.getValue());
			}
			if (name.endsWith(".Max Threads") && (name.contains("Constant Reference Analyzer")
					|| name.contains("Decompiler Switch Analysis") || name.contains("Decompiler Parameter ID"))) {
				setAnalysisOption(currentProgram, name, "1");
				println("set " + name + " = 1");
			}
		}
	}
}
