"""padronização para iniciar o flask por app.py."""

from . import app


if __name__ == "__main__":
    app.run(port=5001, debug=True)
