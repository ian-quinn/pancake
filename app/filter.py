_js_escapes = {
        '\\': '\\u005C',
        '\'': '\\u0027',
        '"': '\\u0022',
        '>': '\\u003E',
        '<': '\\u003C',
        '&': '\\u0026',
        '=': '\\u003D',
        '-': '\\u002D',
        ';': '\\u003B',
        u'\u2028': '\\u2028',
        u'\u2029': '\\u2029'
}
# Escape every ASCII character with a value less than 32.
_js_escapes.update(('%c' % z, '\\u%04X' % z) for z in xrange(32))
def jinja2_escapejs_filter(value):
        retval = []
        for letter in value:
            if _js_escapes.has_key(letter):
                retval.append(_js_escapes[letter])
            else:
                retval.append(letter)
        return jinja2.Markup("".join(retval))
JINJA_ENVIRONMENT.filters['escapejs'] = jinja2_escapejs_filter

