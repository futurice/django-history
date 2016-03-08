import diff_match_patch

def pretty_diff(a, b):
    d = diff_match_patch.diff_match_patch()
    e = d.diff_main(a, b)
    return d.diff_prettyHtml(e)
