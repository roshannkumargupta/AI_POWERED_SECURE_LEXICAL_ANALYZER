import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;
import javax.servlet.http.HttpServletRequest;

public class Calculator {
    public Object evalExpr(HttpServletRequest req) throws Exception {
        String formula = req.getParameter("expr");
        ScriptEngine engine = new ScriptEngineManager().getEngineByName("JavaScript");
        return engine.eval(formula);
    }
}
