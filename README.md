OpenWPM
=======

If you’re a researcher interested in measuring some aspect of online privacy -- whether prevalence of cookies, or leakage of PII, or price discrimination based on personal information, or anything in between -- then the OpenWPM platform is for you.

We built OpenWPM because we noticed that there are an incredible number of methodological and engineering pitfalls in automating web privacy measurement: existing automation tools like Selenium are prone to crashes and data corruption; automated browsing units may not behave sufficiently realistically like human users, and hence measure different results; there can be subtle, unforeseen interactions between different measurement units that may invalidate measurements. These are just a few main ones.

OpenWPM handles all these aspects so you don’t have to. We built it based on a year of our own our hard-earned experience and mistakes in running web privacy measurement studies, our detailed survey of 32 such prior papers, and numerous discussions with researchers in this area. Our crawling infrastructure abstracts away the underlying tools and allows you to specify high-level commands with a minimal amount of code, recovers from all browser crashes, and lets you run reproducible studies. 

See the [wiki](https://github.com/citp/OpenWPM/wiki) for a more in-depth tutorial.
