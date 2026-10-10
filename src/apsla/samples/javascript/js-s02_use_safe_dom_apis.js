element.textContent = value;
element.innerHTML = DOMPurify.sanitize(html);
