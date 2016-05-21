function! Fstrings() range
    let a = tempname()
    let b = tempname()
    exe "%w " . a
    exe "silent! !python3.6 /ssd/home/work/fstrings/fstrings.py " . a:firstline . " " . a:lastline . " < " . shellescape(a) . " > " . shellescape(b)
    redraw!
    exe a:firstline . "," . a:lastline . "d"
    exe (a:firstline - 1) . "r " . b
endfunction

vnoremap = :call Fstrings()<CR>
