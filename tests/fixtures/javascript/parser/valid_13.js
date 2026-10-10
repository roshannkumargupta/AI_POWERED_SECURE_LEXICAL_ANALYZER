class MathUtils {
    static clamp(val, min, max) {
        return Math.min(Math.max(val, min), max);
    }
}
