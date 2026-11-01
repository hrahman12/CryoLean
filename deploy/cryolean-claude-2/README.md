# cryolean-claude-2 (static site + chat function on Vercel)

The public backup site: `site/index.html` plus one Vercel Python function, `api/lanyon.py`, that answers the
website chat with Claude (`cryolean/chat.py`). Lanyon models need the full server (`python -m cryolean serve`),
so the function reports them as skipped.

Deploy (from a scratch folder, so only these files are uploaded):

    cp -r deploy/cryolean-claude-2 /tmp/c2 && cp site/index.html /tmp/c2/ && cp cryolean/chat.py /tmp/c2/api/_chat.py
    cd /tmp/c2 && npx vercel deploy --prod --name cryolean-claude-2

The function needs `ANTHROPIC_API_KEY` set as a Production environment variable in the Vercel project.
