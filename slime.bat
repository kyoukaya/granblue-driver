set start0=python.exe gbf.py profile0 --leechslime
set start1=python gbf.py profile1 --hostslime
START "leech" %start0%
START "host" %start1%
