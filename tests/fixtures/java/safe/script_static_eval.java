import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;

public class FixedEval {
    public Object compute() throws Exception {
        ScriptEngine engine = new ScriptEngineManager().getEngineByName("JavaScript");
        return engine.eval("40 + 2");
    }
}
