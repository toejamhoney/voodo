set mouse=a
" use spaces i/o tabs
set expandtab
set shiftwidth=4
set tabstop=4
set autoindent
set smartindent

" Visual Options
syntax on
colorscheme solarized
set background=dark
" highlight search and incremental search
set hlsearch
set incsearch

filetype plugin on

" line numbers
set number

" show matching brackets
set showmatch

" line wrap
" set nowrap

" search for selection
vnoremap <silent> * :call VisualSelection('f')<CR>
vnoremap <silent> # :call VisualSelection('b')<CR>

set encoding=utf-8
set fileencoding=utf-8

" set colorcolumn to 80
set cc=79

" enable highlighting trailing spaces
"autocmd ColorScheme * highlight ExtraWhitespace ctermfg=red guifg=red
"highlight ExtraWhitespace ctermfg=red guifg=red cterm=bold gui=bold
"match ExtraWhitespace /\s\+$\|\t/
"set list listchars=trail:_

" Code Folding
set foldmethod=indent
set foldnestmax=2
set foldignore=
set foldlevel=1
set foldtext=
