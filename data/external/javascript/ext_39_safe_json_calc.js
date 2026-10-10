function parseCalculationPayload(rawJson) {
    const data = JSON.parse(rawJson);
    return Number(data.operandA) + Number(data.operandB);
}
