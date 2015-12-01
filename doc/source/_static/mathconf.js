// MathJaX customization, custom commands etc.
MathJax.Hub.Config({
  "HTML-CSS": {
      //availableFonts: ["Neo-Euler"], preferredFont: "Neo-Euler",
      //webFont: "Neo-Euler",
      //scale: 85, // Euler is a bit big.
      mtextFontInherit: true,
      matchFontHeight: true,
      scale: 90, // STIX is a bit big.

  },
  // This is not working for some reason.
  "TeX": {
    Macros: {
        d: ["\\mathrm{d}"],
        I: ["\\mathrm{i}"],
        vect: ["\\vec{#1}", 1],
        uvect: ["\\hat{#1}", 1],
        abs: ["\\lvert#1\\rvert", 1],
        Abs: ["\\left\\lvert#1\\right\\rvert", 1],
        norm: ["\\lVert#1\\rVert", 1],
        Norm: ["\\left\\lVert#1\\right\\rVert", 1],
        ket: ["|#1\\rangle", 1],
        bra: ["\\langle#1|", 1],
        Ket: ["\\left|#1\\right\\rangle", 1],
        Bra: ["\\left\\langle#1\\right|", 1],
        braket: ["\\langle#1\\rangle", 1],
        op: ["\\mathbf{#1}", 1],
        mat: ["\\mathbf{#1}", 1],
        pdiff: ["\\frac{\\partial^{#1} #2}{\\partial {#3}^{#1}}", 3, ""],
        diff: ["\\frac{\\d^{#1} #2}{\\d {#3}^{#1}}", 3, ""],
        ddiff: ["\\frac{\\delta^{#1} #2}{\\delta {#3}^{#1}}", 3, ""],
        erf: "\\mathop{\\mathrm{erf}}\\nolimits",
        order: "\\mathop{\\mathcal{O}}\\nolimits",
        diag: "\\mathop{\\mathrm{diag}}\\nolimits",
        floor: ["\\left\\lfloor#1\\right\\rfloor", 1],
        ceil: ["\\left\\lceil#1\\right\\rceil", 1],

        mylabel: ["\\label{#1}\\tag{#1}", 1],
        degree: ["^{\\circ}"],
    },
  }
});
