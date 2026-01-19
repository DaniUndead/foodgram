import '@testing-library/jest-dom';

global.setImmediate = (fn, ...args) => setTimeout(fn, 0, ...args);
global.clearImmediate = (id) => clearTimeout(id);