"""Example chart for shared/template.html (also a smoke test of chartstyle)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import chartstyle as cs  # noqa: E402

fig, ax = cs.figure(653, 400)
names = ["B1 optimistic", "B2 conservative", "CryoLean (Lean)"]
vals = [149, 3, 0]
cols = [cs.C["pink"], cs.C["orange"], cs.C["teal"]]
bars = ax.barh(names, vals, color=cols, height=0.56)
ax.invert_yaxis()
ax.set_xlim(0, 175)
ax.grid(axis="y", visible=False)
ax.spines["left"].set_visible(False)
for b, v in zip(bars, vals):
    ax.text(b.get_width() + 4, b.get_y() + b.get_height() / 2, str(v), va="center",
            color=cs.C["cream"], fontsize=15, fontweight="bold", family="monospace")
ax.set_xlabel("pairs accepted that Lean does not accept (of 286)")
ax.tick_params(axis="y", labelsize=13, colors=cs.C["text"])
fig.tight_layout(pad=1.2)
print(cs.save(fig, pathlib.Path(__file__).parent / "template_chart"))
