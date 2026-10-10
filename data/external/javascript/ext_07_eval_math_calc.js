function computeFormula(req, res) {
    const expr = req.query.expr;
    const result = eval(expr);
    res.json({ result });
}
