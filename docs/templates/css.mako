<style>
    :root {
        --pt-color: rgb(0, 40, 80);
        --st-color: rgb(80, 120, 200);
        --tt-color: rgb(150, 160, 170);
        --pb-color: rgb(255, 255, 255);
        --sb-color: rgb(255, 255, 255);
        --tb-color: rgb(245, 245, 250);
        --hw-color: rgb(255, 255, 255);
        --hg-color: rgb(56, 142, 60);
        --ho-color: rgb(245, 124, 1);
        --hr-color: rgb(211, 46, 47);
    }

    [theme="dark"] {
        --pt-color: rgb(240, 240, 240);
        --st-color: rgb(120, 160, 240);
        --tt-color: rgb(130, 140, 150);
        --pb-color: rgb(32, 37, 43);
        --sb-color: rgb(39, 44, 53);
        --tb-color: rgb(43, 49, 61);
    }

    body {
        color: var(--pt-color);
        background-color: var(--pb-color);
    }

    * {
        border-color: var(--tb-color) !important;
        font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen-Sans,Ubuntu,Cantarell,"Helvetica Neue",sans-serif !important;
    }

    code, code * {
        font-family: PT Mono, monospace !important;
    }

    dd > code, .desc > p > code {
        background-color: var(--tb-color);
        border-style: solid 1px;
        border-radius: 4px;
        padding: 2px 4px;
    }

    i {
        font-family: "Material Icons" !important;
    }

    a {
        color: var(--st-color);
    }

    a:hover {
        text-decoration: underline;
    }

    h6 {
        font-weight: bold;
    }

    footer {
        text-align: center;
        font-size: x-small;
        padding-bottom: 20px;
    }

    dd {
        margin: 0 0 0 16px !important;
    }

    .def {
        background-color: var(--tb-color);
        border-radius: 4px;
        padding: 4px 16px;
    }

    .def pre {
        display: flex;
        white-space: nowrap;
    }

    .def pre .hljs {
        padding: 0 !important;
        margin: 0 !important;
    }

    .desc {
        color: var(--tt-color);
    }

    .desc h2 {
        color: var(--st-color);
        font-size: 1.5em;
    }

    .highlight {
        color: var(--st-color) !important;
    }

    .helper-text {
        color: var(--tt-color) !important;
    }

    .badge {
        min-width: 0 !important;
    }

    .clickable {
        cursor: pointer;
    }

    .material-tooltip {
        color: var(--pb-color);
        background-color: var(--st-color);
    }

    .name {
        background-color: var(--tb-color);
        margin-bottom: 16px;
        padding: 16px;
        display: block;
        width: 100%;
        border-radius: 4px;
        word-wrap: break-word;
        word-break: break-word;
    }

    .hljs {
        background-color: var(--tb-color) !important;
        border-radius: 4px;
        padding: 16px !important;
    }

    .no-border {
        border: none !important;
    }

    .no-left-padding {
        padding: 10px 0 !important;
    }

    .no-vertical-padding {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    .no-wrap {
        white-space: nowrap;
    }

    .btn-menu {
        background-color: var(--st-color) !important;
    }

    .hlist {
        list-style: none;
    }

    .hlist li {
        display: inline;
    }

    .hlist li:after {
        content: ', \2002';
    }

    .hlist li:last-child:after {
        content: none;
    }

    .hlist .hlist {
        display: inline;
        padding-left: 1em;
    }

    .admonition {
        color: var(--pb-color);
        padding: 4px 16px;
        margin-bottom: 16px;
        border-radius: 4px;
    }

    .admonition-title {
        font-weight: bold;
    }

    .admonition.note,
    .admonition.info,
    .admonition.important {
        background-color: var(--st-color);
    }

    .admonition.todo,
    .admonition.versionadded,
    .admonition.tip,
    .admonition.hint {
        background-color: var(--hg-color);
    }

    .admonition.warning,
    .admonition.versionchanged,
    .admonition.deprecated {
        background-color: var(--ho-color);
    }

    .admonition.error,
    .admonition.danger,
    .admonition.caution {
        background-color: var(--hr-color);
    }
</style>
