function! Fstrings() range
    let a = tempname()
    let b = tempname()
    exe "%w " . a
    let d = expand("<sfile>:p:h")
    if executable('python3.6')
        let p = 'python3.6'
    elseif executable('python3')
        let p = 'python3'
    else
        let p = 'python'
    endif
    exe "silent! !" . shellescape(p) . " " . shellescape(d) . "/fstrings.py " . a:firstline . " " . a:lastline . " < " . shellescape(a) . " > " . shellescape(b)
    redraw!
    exe a:firstline . "," . a:lastline . "d"
    exe (a:firstline - 1) . "r " . b
endfunction

vnoremap = :call Fstrings()<CR>
