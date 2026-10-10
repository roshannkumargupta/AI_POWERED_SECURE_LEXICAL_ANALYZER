const numbers = [1, 2, 3, 4, 5];
const evens = numbers.filter(n => n % 2 === 0);
const doubled = evens.map(n => n * 2);
console.log(doubled);
