function adler32(data) {
    var modulo = 65521,
    	a = 1, b = 0,
    	idx;

    for (idx = 0; idx < data.length; ++idx) {
        a = (a + data[idx]) % modulo;
        b = (b + a) % modulo;
    }
    return (a | (b << 16)) >>> 0;
}