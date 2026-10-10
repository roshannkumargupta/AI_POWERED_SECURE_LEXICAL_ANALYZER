class Service { #ready = true; async read(item) { return item?.name ?? "ready"; } *items() { yield this.#ready; } }
