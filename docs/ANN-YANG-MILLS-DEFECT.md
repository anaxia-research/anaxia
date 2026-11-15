# Sharp time doubling for the thermal defect

Let a positive compact transfer operator have a simple largest eigenvalue and finite trace at integer time $T$. Let its other eigenvalue ratios, raised to the $T$th power, be $x_j$. Put $D=\sum_jx_j$, $E=\sum_jx_j^2$, and $F=\sum_jx_j^4$. Write $Z(T)=1+D$ after vacuum normalization. The defect $\Psi(T)=2\log Z(T)-\log Z(2T)$ is unchanged by the normalization. All traces are on the same spatial box and at the same coupling. [One-scale criterion](YANG-MILLS-ONE-SCALE.md) · [Source manuscript](https://www.preprints.org/manuscript/202611.1282)

## Sharp contraction

Let $R=e^{\Psi(T)}=(1+D)^2/(1+E)$ and $a=R-1<1$. Since $E\le D$, we have $D\le a<1$. The inequality $E\le D^2$ gives $a\ge 2D/(1+D^2)$, hence $D\le d_*=a/(1+\sqrt{1-a^2})$. One positive excited weight $d_*$ attains equality.

If $D=0$, all defects vanish. Otherwise Jensen's inequality with weights $x_j/D$ and the convex function $v\mapsto v^3$ gives $F\ge E^3/D^2$. At fixed $R$ this yields

$$
e^{\Psi(2T)}\le U(D)=\frac{(1+E)^2}{1+E^3/D^2},\qquad E=\frac{(1+D)^2}{R}-1.
$$

On the feasible interval $\sqrt R-1\le D\le d_*$, we have $0\le E\le D^2$ by monotonicity of $2D/(1+D^2)$ for $D<1$. The logarithmic derivative of $U$, multiplied by $(1+D)(D^2+E^3)$, is $4D^2-6E^2+2E^3/D$. The function $E^2(3-E/D)$ increases on $0\le E\le D^2$ and at the endpoint is $D^4(3-D)\le2D^2$. Thus $U$ is increasing. At $D=d_*$ we have $E=d_*^2$ and obtain

$$
e^{\Psi(2T)}-1\le\frac{a^2}{2-a^2}.
$$

The same one-excitation spectrum gives equality. This propagates small defect on a fixed finite box. Spatial cutting and the continuum step still require a bound uniform across boxes and couplings.

## A larger sufficient defect seed

For $0\le\Psi\le u<1$, the identity $2\log Z(T)=\Psi+\log(1+E)$ and $E\le D^2\le(e^\Psi-1)^2$ give

$$
\log Z(T)\le\tfrac12\big[\Psi+(e^\Psi-1)^2\big]
\le\tfrac12\left(1+\frac{u}{(1-u)^2}\right)\Psi.
$$

Use $e^\Psi-1\le\Psi/(1-\Psi)$ for the last inequality. If each side of the rectangular box lies in $[2T,40T)$, the hypothetical defect bound $\Psi\le V/(13{,}510{,}000T^3)$ permits $u=32/6755$. The converted pressure coefficient is exactly $2906552896/2907784899$ times the allowed coefficient $1/26{,}880{,}000$ from the third row of the one-scale criterion. A proof of that uniform weak-coupling defect seed and a matching continuum construction remain outstanding.

```sh
python anaxia.py ann run --target yang-mills --exploration wide --tasks 44
```

The worker checks the rational seed conversion, replays contraction on multilevel spectra, and verifies equality on one-level spectra. The proof above establishes the estimate for the entire stated class.
