<%
    import os

    import pdoc
    from pdoc.html_helpers import extract_toc, glimpse, to_html as _to_html, format_git_link


    def link(dobj: pdoc.Doc, name=None):
        name = name or dobj.qualname + ('()' if isinstance(dobj, pdoc.Function) else '')
        if isinstance(dobj, pdoc.External) and not external_links:
            return name
        url = dobj.url(relative_to=module, link_prefix=link_prefix, top_ancestor=not show_inherited_members)
        return '<a title="{}" href="{}">{}</a>'.format(dobj.refname, url, name)


    def to_html(text):
        return _to_html(text, docformat=docformat, module=module, link=link, latex_math=latex_math)


    def get_annotation(bound_method, sep=':'):
        annot = show_type_annotations and bound_method(link=link) or ''
        if annot:
            annot = ' ' + sep + '\N{NBSP}' + annot
        return annot
%>

<%def name="show_desc(d, short=False)">
    <%
    inherits = ' inherited' if d.inherits else ''
    docstring = glimpse(d.docstring) if short or inherits else d.docstring
    %>
    % if d.inherits:
    <p class="inheritance">
        <em>Inherited from:</em>
        % if hasattr(d.inherits, 'cls'):
        <code>${link(d.inherits.cls)}</code>.<code>${link(d.inherits, d.name)}</code>
        % else:
        <code>${link(d.inherits)}</code>
        % endif
    </p>
    % endif
    <div class="desc${inherits}">${docstring | to_html}</div>
</%def>

<%def name="show_module_list(modules)">
<h4>Python module list</h4>

% if not modules:
    <p>No modules found.</p>
% else:
    <dl id="http-server-module-list">
    % for name, desc in modules:
        <div class="flex">
            <dt><a href="${link_prefix}${name}">${name}</a></dt>
            <dd>${desc | glimpse, to_html}</dd>
        </div>
    % endfor
    </dl>
% endif
</%def>

<%def name="show_column_list(items)">
    <ul class="collection no-border">
    % for item in items:
        <li class="collection-item transparent no-border no-vertical-padding">
            <code>${link(item, item.name)}</code>
        </li>
    % endfor
    </ul>
</%def>

<%def name="show_source(d)">
    <% git_link = format_git_link(git_link_template, d) %>
    % if git_link:
    <span class="badge">
        <a href="${git_link}" target="_blank">
            <i class="material-icons clickable highlight tooltipped" data-position="top" data-tooltip="View on GitHub">open_in_new</i>
        </a>
    </span>
    % endif
</%def>

<%def name="show_module(module)">
    <%
    variables = module.variables(sort=sort_identifiers)
    classes = module.classes(sort=sort_identifiers)
    functions = module.functions(sort=sort_identifiers)
    submodules = module.submodules()
    %>

    <%def name="show_func(f)">
    <dt id="${f.refname}" class="def">
        <pre>
            <code class="python flex name">
                <%
                params = f.params(annotate=show_type_annotations, link=link)
                return_type = get_annotation(f.return_annotation, '\N{non-breaking hyphen}>')
                %>

                ${f.funcdef()} ${f.name}${'(<br>' if len(params) > 3 else '(' + ', '.join(params) + ')'}
                % if len(params) > 3:
                % for p in params:
                &nbsp&nbsp&nbsp&nbsp${p},<br>
                % endfor
                )
                % endif
                ${return_type}
            </code>
            ${show_source(f)}
        </pre>
    </dt>
    <dd>${show_desc(f)}</dd>
    </%def>

    <header>
        <ul class="collection with-header no-border">
            <li class="collection-header transparent no-border no-left-padding">
                <h4>
                    ${'Namespace' if module.is_namespace else  \
                      'Package' if module.is_package and not module.supermodule else \
                      'Module'} ${module.name}
                </h4>
                <section id="section-intro" class="helper-text">
                ${module.docstring | to_html}
                </section>
            </li>
        </ul>
    </header>

    <section>
    % if submodules:
        <h5 class="section-title" id="header-submodules">Sub-modules</h5>
        <dl>
        % for m in submodules:
            <dt><code class="name">${link(m)}</code></dt>
            <dd>${show_desc(m, short=True)}</dd>
        % endfor
        </dl>
    % endif
    </section>

    <section>
    % if variables:
        <h5 class="section-title" id="header-variables">Global variables</h5>
        <dl>
        % for v in variables:
            <% return_type = get_annotation(v.type_annotation) %>
            <dt id="${v.refname}"><code class="name">var ${v.name}${return_type}</code></dt>
            <dd>${show_desc(v)}</dd>
        % endfor
        </dl>
    % endif
    </section>

    <section>
    % if functions:
        <h5 class="section-title" id="header-functions">Functions</h5>
        <dl>
        % for f in functions:
            ${show_func(f)}
        % endfor
        </dl>
    % endif
    </section>

    <section>
    % if classes:
        <h5 class="section-title" id="header-classes">Classes</h5>
        <dl>
        % for c in classes:
            <%
            class_vars = c.class_variables(show_inherited_members, sort=sort_identifiers)
            smethods = c.functions(show_inherited_members, sort=sort_identifiers)
            inst_vars = c.instance_variables(show_inherited_members, sort=sort_identifiers)
            methods = c.methods(show_inherited_members, sort=sort_identifiers)
            mro = c.mro()
            subclasses = c.subclasses()
            params = c.params(annotate=show_type_annotations, link=link)
            %>
            <dt id="${c.refname}" class="def">
                <pre>
                    <code class="python flex name class">
                        class ${c.name}${'(<br>' if len(params) > 3 else '(' + ', '.join(params) + ')' if params else ''}
                        % if len(params) > 3:
                        % for p in params:
                        &nbsp&nbsp&nbsp&nbsp${p},<br>
                        % endfor
                        )
                        % endif
                    </code>
                    ${show_source(c)}
                </pre>
            </dt>

            <dd>${show_desc(c)}

            % if mro:
            <h6>Ancestors</h6>
            <ul class="hlist">
            % for cls in mro:
                <li>${link(cls)}</li>
            % endfor
            </ul>
            %endif

            % if subclasses:
            <h6>Subclasses</h6>
            <ul class="hlist">
            % for sub in subclasses:
                <li>${link(sub)}</li>
            % endfor
            </ul>
            % endif
            % if class_vars:
            <h6>Class variables</h6>
            <dl>
            % for v in class_vars:
                <% return_type = get_annotation(v.type_annotation) %>
                <dt id="${v.refname}"><code class="name">var ${v.name}${return_type}</code></dt>
                <dd>${show_desc(v)}</dd>
            % endfor
            </dl>
            % endif
            % if smethods:
            <h6>Static methods</h6>
            <dl>
            % for f in smethods:
                ${show_func(f)}
            % endfor
            </dl>
            % endif
            % if inst_vars:
            <h6>Instance variables</h6>
            <dl>
            % for v in inst_vars:
                <% return_type = get_annotation(v.type_annotation) %>
                <dt id="${v.refname}"><code class="name">var ${v.name}${return_type}</code></dt>
                <dd>${show_desc(v)}</dd>
            % endfor
            </dl>
            % endif
            % if methods:
            <h6>Methods</h6>
            <dl>
            % for f in methods:
                ${show_func(f)}
            % endfor
            </dl>
            % endif

            % if not show_inherited_members:
            <% members = c.inherited_members() %>
            % if members:
                <h6>Inherited members</h6>
                <ul class="hlist">
                % for cls, mems in members:
                    <li><code><b>${link(cls)}</b></code>:
                        <ul class="hlist">
                        % for m in mems:
                            <li><code>${link(m, name=m.name)}</code></li>
                        % endfor
                        </ul>
                    </li>
                % endfor
                </ul>
            % endif
            % endif
            </dd>
        % endfor
        </dl>
    % endif
    </section>
</%def>

<%def name="module_index(module)">
  <%
  variables = module.variables(sort=sort_identifiers)
  classes = module.classes(sort=sort_identifiers)
  functions = module.functions(sort=sort_identifiers)
  submodules = module.submodules()
  supermodule = module.supermodule
  %>
  <div id="sidebar">

    <%include file="logo.mako"/>

    <ul id="index" class="collection with-header no-border">
    <li class="collection-header transparent">
        <h4>Index</h4>
    </li>
    ${extract_toc(module.docstring) if extract_module_toc_into_sidebar else ''}

    % if supermodule:
    <li class="collection-header transparent no-border no-vertical-padding">
        <h5><a href="#header-supermodule">Super-module</a></h5>
        ${show_column_list([supermodule])}
    </li>
    % endif

    % if submodules:
    <li class="collection-header transparent no-border no-vertical-padding">
        <h5><a href="#header-submodules">Sub-modules</a></h5>
        ${show_column_list(submodules)}
    </li>
    % endif

    % if variables:
    <li class="collection-header transparent no-border no-vertical-padding">
        <h5><a href="#header-variables">Global variables</a></h5>
        ${show_column_list(variables)}
    </li>
    % endif

    % if functions:
    <li class="collection-header transparent no-border no-vertical-padding">
        <h5><a href="#header-functions">Functions</a></h5>
        ${show_column_list(functions)}
    </li>
    % endif

    % if classes:
    <li class="collection-header transparent no-border no-vertical-padding">
        <h5><a href="#header-classes">Classes</a></h5>
        <ul class="collection with-header no-border">
        % for c in classes:
            <li class="collection-header transparent no-border no-vertical-padding">
                <b><code>${link(c)}</code></b>
                <%
                members = c.functions(sort=sort_identifiers) + c.methods(sort=sort_identifiers)
                if list_class_variables_in_index:
                    members += (c.instance_variables(sort=sort_identifiers) +
                                c.class_variables(sort=sort_identifiers))
                if not show_inherited_members:
                    members = [i for i in members if not i.inherits]
                if sort_identifiers:
                    members = sorted(members)
                %>
                % if members:
                    ${show_column_list(members)}
                % endif
            </li>
        % endfor
        </ul>
    </li>
    % endif

    </ul>
  </div>
</%def>

<!doctype html>
<html lang="${html_lang}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1" />
    <link rel="stylesheet" href="https://feeltheajf.github.io/materialize/materialize.min.css" integrity="sha256-kpeCd0c1zTgJMsU+s8Pz4CwckI73qwpdYMTxTsRyO8A=" crossorigin>
    <script src="https://feeltheajf.github.io/materialize/materialize.min.js" integrity="sha256-U/cHDMTIHCeMcvehBv1xQ052bPSbJtbuiw4QA9cTKz0=" crossorigin></script>
    <%include file="css.mako"/>

    <% module_list = 'modules' in context.keys() %>

    % if module_list:
    <title>Python module list</title>
    <meta name="description" content="A list of documented Python modules." />
    % else:
    <title>${module.name} API documentation</title>
    <meta name="description" content="${module.docstring | glimpse, trim, h}" />
    % endif

    % if syntax_highlighting:
    <link id="hljs-style">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js" integrity="sha256-Uv3H6lx7dJmRfRvH8TH6kJD1TSK1aFcwgx+mdg3epi8=" crossorigin></script>
    % endif

    <script>
        const dark = 'dark';
        const light = 'light';

        function scannerHelp() {
            window.open('https://github.com/feeltheajf/trufflehog3');
        }

        function getTheme() {
            return document.documentElement.getAttribute('theme');
        }

        function setTheme(theme, noHighlighting) {
            document.documentElement.setAttribute('theme', theme);
            if (!noHighlighting) {
                initHighlighting();
            }
        }

        function switchTheme(noHighlighting) {
            const theme = getTheme() == light ? dark : light;
            localStorage.setItem('theme', theme);
            setTheme(theme, noHighlighting);
        }

        function initHighlighting() {
            document.head.removeChild(document.getElementById('hljs-style'));
            const theme = getTheme() == dark ? dark : light;
            const link = document.createElement('link');
            link.id = 'hljs-style';
            link.rel = 'stylesheet preload';
            link.as = 'style';
            link.href = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/atom-one-' + theme + '.min.css';
            document.getElementsByTagName('HEAD')[0].appendChild(link);
            hljs.initHighlighting();
        }

        const browserTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? dark : light;
        const theme = localStorage.getItem('theme') || browserTheme;
        setTheme(theme, true);
    </script>
</head>
<body>
    <div class="fixed-action-btn">
        <a class="btn-floating btn-menu"><i class="material-icons">menu</i></a>
        <ul>
            <li><a class="btn-floating purple" onclick="scannerHelp()"><i class="material-icons">help</i></a></li>
            <li><a class="btn-floating yellow" onclick="switchTheme()"><i class="material-icons">brightness_medium</i></a></li>
        </ul>
    </div>
    <div class="row main">
        % if module_list:
        <div class="col s12">
            <article id="content">
            ${show_module_list(modules)}
            </article>
        </div>
        % else:
        <div class="col s12 m12 l3">
            ${module_index(module)}
        </div>
        <div class="col s12 m12 l7 offset-l1">
            <article id="content">
            ${show_module(module)}
            </article>
        </div>
        % endif
    </div>
    <footer>
        <p class="helper-text">
            Generated by <a href="https://pdoc3.github.io/pdoc">pdoc</a>
        </p>
    </footer>

    <script>
        M.AutoInit();
        document.addEventListener('DOMContentLoaded', function () {
            M.FloatingActionButton.init(
                document.querySelector('.fixed-action-btn'), {
                    hoverEnabled: false
                }
            );

            initHighlighting();
        });

        % if http_server and module:
        setInterval(() =>
            fetch(window.location.href, {
                method: 'HEAD',
                cache: 'no-store',
                headers: {'If-None-Match': '${os.stat(module.obj.__file__).st_mtime}'},
            }).then(response => response.ok && window.location.reload()), 700);
        % endif
    </script>
</body>
</html>
