autoCSP
=======

CSP-injecting reverse HTTP proxy

Based on my bachelor thesis, this reverse HTTP proxy can be used to add [Content
Security Policy](http://www.w3.org/TR/CSP/#introduction) headers to web
applications which do not support them, yet. All policy generation is done
automatically and is likely to be robust. As a secure CSP requires inline code
and eval-like constructs to be removed from the markup, the proxy attempts to do
so. The results of this are pretty good for a lot of inline code, but all
dynamically changing inline code cannot be securely rewritten. Furthermore, the
rewriting of eval-like constructs is only rudimentary and will only be able to
rewrite them in the case they are used to parse JSON.

Abstract
========
> As the Internet gains wide adoption, the World Wide Web becomes one of the
> most important sources of information worldwide. Highly distributed networks
> serve millions of clients every day. In consequence of this popularity, user
> agents increased in complexity over the years, while still maintaining the
> technological burdens of their early days. Core security issues were left
> untouched by browser vendors and standards bodies. This led to a wide range of
> possible client-side attacks today. By default, there are only a few
> limitations to the capabilities of web documents. Accordingly, user agents
> shift the responsibility to protect from client-side attacks to web
> applications.

> In an attempt to give web applications the possibility of limiting these
> capabilities, Sterne et al. proposed Content Security Policy in 2010. It
> enables fine grained policies, strictly controlling the allowed resources and
> other properties of web documents. As a result of that, it is able to reduce
> the attack surface of a web application in a substantial way. This comes at
> the cost of breaking compatibility with all websites using inline code and
> eval -like constructs. In order to use secure policies, these have to be
> rewritten. Therefore, deploying CSP may not always be feasible. Furthermore,
> policy generation introduces a lot of pitfalls because it leaves the decision,
> which resources (or resource types) might harm client-side security, to the
> web application. Thus, it is easily possible to create too broad policies, not
> increasing the security at all. This thesis presents a reverse HTTP proxy,
> which is able to infer restrictive CSPs for arbitrary web applications. It
> externalizes inline code automatically in a secure way and attempts to replace
> calls to eval-like constructs. Overall, it allows web applications to adopt
> CSP without any changes to server-side code.

Is this proxy useful for me?
============================
Depends on many factors. If you have a high profile site, probably no. It was
not built with performance in mind and is merely a proof of concept. You may use
any idea of the thesis or this proxy and implement it in your
framework/product/foo. If you feel adventurous, you might try and use it on your
site (it only supports Chrome right now). I might even help you, but I
personally think that the ideas and concepts will be more useful when
incorporated in a framework to aid developers. I will look into such projects
very soon.

