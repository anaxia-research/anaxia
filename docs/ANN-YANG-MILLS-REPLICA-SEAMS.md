# A two-seam identity for the Wilson thermal defect

On a spatial torus \(s=(s_1,s_2,s_3)\), write \(V=s_1s_2s_3\). Let \(Z_\beta(s,T)\) be the Wilson partition function with periodic time of integer length \(T\ge3\), compact gauge group, and normalized Haar link measures. Use the same coupling \(\beta\) at both time lengths. The finite quantity needed by the one-scale argument is

\[
\Psi_\beta(s,T)=2\log Z_\beta(s,T)-\log Z_\beta(s,2T).
\]

The identity below expresses \(\Psi_\beta\) as the integrated connected response of two local seam perturbations. It holds at every finite coupling and for rectangular integer sides, including sides that do not admit a prescribed blocking factor. The estimates that would make it uniform along the continuum tuning are stated separately.

Replica gluing and free-energy interpolation are established methods for entanglement Rényi calculations. Here both seams span the full spatial torus and their mixed response gives the thermal defect at fixed coupling. [Gauge-theory replica calculations](https://arxiv.org/abs/2211.00425) · [Thermodynamic interpolation](https://journals.aps.org/prresearch/abstract/10.1103/PhysRevResearch.4.L032002)

## The two-seam Wilson measure

Take two sheets of the time-\(T\) lattice. Each vertex, spatial link, and temporal link away from the cuts carries a sheet label in \(\{0,1\}\). Choose two distinct cuts \(a,b\), between consecutive time slices, at distance \(d=\lfloor T/2\rfloor\) in the cyclic time coordinate. At either cut use two independent bundles of temporal links:

- A straight link goes from sheet \(i\) below the cut to sheet \(i\) above it.
- A swapped link goes from sheet \(i\) below the cut to sheet \(1-i\) above it.

Each of the two matching choices gives a full collection of temporal plaquettes at the cut. For a bottom spatial link on sheet \(i\), both vertical edges in its plaquette belong to the chosen matching and the top spatial link belongs to the matched sheet. Every term is the usual Wilson exponent of a closed plaquette, so independent vertex gauge transformations on both sheets preserve every term. The independent bundles let the interpolated model keep this gauge invariance while allowing the unused bundle to integrate to one at each endpoint.

At cut \(c\in\{a,b\}\) denote the sums of the Wilson exponent terms, including the coupling, by \(S_c^{\rm str}\) and \(S_c^{\rm sw}\). Put \(\Delta_c=S_c^{\rm sw}-S_c^{\rm str}\). Keep the usual Wilson exponent for every other plaquette on both sheets. Add the cut terms

\[
S_a^{\rm str}+u\Delta_a+S_b^{\rm str}+v\Delta_b,
\qquad 0\le u,v\le1 .
\]

Write \(F(u,v)\) for the log partition function on this fixed link space and \(\operatorname{Cov}_{u,v}\) for the covariance with respect to its normalized measure.

## Exact covariance identity

With no swap, the active link graph is the disjoint union of two time-\(T\) tori. With one swap, following the successive matchings around the time circle interchanges the two sheets. The active graph then has a single time cycle of length \(2T\). With two swaps, the composition around the circle is again the identity. More explicitly, the active temporal edges define a permutation of the \(2T\) pairs of time and sheet. At each spatial site the same permutation applies. Its cycles are the time coordinates of the connected tori, and all spatial edges and plaquettes are carried along by this relabeling. The inactive links occur in no exponent term and integrate to one. Thus

\[
F(0,0)=F(1,1)=2\log Z_\beta(s,T),\qquad
F(1,0)=F(0,1)=\log Z_\beta(s,2T).
\]

All terms in the finite-volume integral are bounded on the compact link space, so differentiation under the integral gives \(\partial_u\partial_v F=\operatorname{Cov}_{u,v}(\Delta_a,\Delta_b)\). Integrating over the unit square yields

\[
\boxed{\displaystyle
\Psi_\beta(s,T)=\frac12\int_0^1\int_0^1
\operatorname{Cov}_{u,v}(\Delta_a,\Delta_b)\,du\,dv.}
\]

At cut \(a\) allocate each plaquette term to its bottom spatial site, adding the three spatial orientations and both sheet labels at that site to form a local difference \(A_x\). Do the same at cut \(b\) to form \(B_y\). Because the interpolation preserves spatial translations, the exact response per spatial volume is

\[
\frac{\Psi_\beta(s,T)}{V}=
\frac12\int_0^1\int_0^1
\sum_{y\in s}\operatorname{Cov}_{u,v}(A_0,B_y)\,du\,dv.
\]

The integral here is signed. Bounding it directly can retain cancellations that an absolute covariance estimate discards. An alternative is to integrate the cut links first. The two cut bundles are independent given all other links, so each cut difference in the covariance can be replaced by its conditional mean given the spatial links. That mean is the derivative of the log of its integrated cut weight and depends only on the two spatial slices adjacent to the cut.

## A sufficient quantitative estimate

The improved one-scale allowance is \(\Psi_\beta(s,T)\le V/(13{,}510{,}000\,T^3)\) over the full window of spatial sides in \([2T,40T)\). By the identity, the remaining Wilson input is an upper bound \(2/(13{,}510{,}000\,T^3)\) on the integrated summed response above, uniformly in the required cutoffs and rectangles at the selected base time. [One-scale pressure argument](YANG-MILLS-ONE-SCALE.md)

For example, take an effective length \(b\ge1\) in lattice units and suppose one could prove, with \(C,m>0\) independent of cutoff, shape, and interpolation parameters, that

\[
|\operatorname{Cov}_{u,v}(A_0,B_y)|\le
C b^{-6}\exp[-m(d+\operatorname{dist}_s(0,y))/b],
\]

where \(\operatorname{dist}_s\) is the periodic spatial \(\ell^1\) distance. In each cyclic coordinate, at most two sites lie at any given positive distance. Consequently

\[
\sum_{y\in s}e^{-m\operatorname{dist}_s(0,y)/b}
\le \left(1+\frac{2}{e^{m/b}-1}\right)^3
\le b^3(1+2/m)^3.
\]

Write \(h=T/b\). Since \(d\ge(T-1)/2\) and \(b\ge1\), a sufficient scalar inequality is

\[
\frac{T^3\Psi_\beta(s,T)}{V}
\le \frac C2 (1+2/m)^3 e^{m/2}\,h^3e^{-mh/2}
\le \frac{1}{13{,}510{,}000}.
\]

The function \(h^3 e^{-mh/2}\) decreases for \(h\ge6/m\). A cutoff-independent choice of \(h\) can therefore meet the scalar bound if the covariance estimate is valid on the required boxes and the chosen \(T\) lies within the available physical time window. Summing the spatial correlations costs a factor of order \(b^3\). A decay rate on the scale \(b\) without control of the covariance amplitudes does not yield the displayed seed.

## An alternative with bounded observables

On the same link space, put an independent fair prior on a sign at each cut. A sign of \(+1\) selects the swapped matching and a sign of \(-1\) selects the straight matching. Reweight the signs and link variables by the selected Wilson exponent. The four endpoint identities give weight \(Z_\beta(s,T)^2\) to each pair of equal signs and \(Z_\beta(s,2T)\) to each pair of unequal signs, up to the same normalization. Each sign has mean zero and their correlation is

\[
\mathbb E[\sigma_a\sigma_b]
=\frac{Z_\beta(s,T)^2-Z_\beta(s,2T)}
{Z_\beta(s,T)^2+Z_\beta(s,2T)}
=\tanh(\Psi_\beta(s,T)/2).
\]

Given the links, the signs are independent and \(\mathbb E[\sigma_c\mid\text{links}]=\tanh(\Delta_c/2)=:m_c\). Thus the same correlation is \(\operatorname{Cov}(m_a,m_b)\) under the link measure whose factor at cut \(c\) is \(e^{S_c^{\rm str}}+e^{S_c^{\rm sw}}\). The observables \(m_c\) are bounded by one independently of the coupling. A uniform upper bound of \(\tanh(4/13{,}510{,}000)\) on this covariance suffices for the seed throughout the window, since \(V/T^3\ge8\). The cut weights in this measure couple all sites on each seam. The remaining estimate therefore concerns separated extended observables in the corresponding ensemble.

## Massless Gaussian control

On the smallest spatial cube, with side \(2T\), take one nonzero Fourier mode of the massless nearest-neighbor Gaussian transfer theory. Its spatial Laplacian eigenvalue is \(4\sin^2(\pi/(2T))\). The time difference equation gives

\[
\cosh E=1+2\sin^2(\pi/(2T)),\qquad
E=2\,\operatorname{arsinh}(\sin(\pi/(2T)))\le\pi/T.
\]

Keep the even Fock tower of this one oscillator and normalize its vacuum eigenvalue to one. With \(q=e^{-2TE}\), the resulting traces are \(1/(1-q)\) at \(T\) and \(1/(1-q^2)\) at \(2T\). Its thermal defect is

\[
\log\frac{1+q}{1-q}\ \ge\ 2q\ >\ \frac{2}{3^7}\ >\
\frac{8}{13{,}510{,}000}.
\]

The series for the logarithm gives the first inequality. The second uses \(2TE\le2\pi<7\) and \(e<3\). The last comparison is rational, and the rightmost term equals the target seed on the volume \(V=(2T)^3\). For a free mode with global adjoint color symmetry, the invariant quadratic form supplies an even singlet tower via repetitions of the pair-creation operator contracted with the invariant metric. This is a Gaussian benchmark on the indicated tower. It shows why a massless Gaussian comparison needs to account for a low-energy even sector, in addition to single-particle modes. [One-scale source, Proposition 7.73](https://www.preprints.org/manuscript/202611.1282)

The identity proves exact cancellation of the bulk free energy in the response representation. The uniform seam estimate at weak coupling and the construction of a matching nontrivial continuum theory remain open. Both are needed to use this route for the Yang–Mills existence and mass-gap problem. [One-scale source, Proposition 7.57 and Theorem F](https://www.preprints.org/manuscript/202611.1282) · [Clay problem statement](https://www.claymath.org/wp-content/uploads/2022/06/yangmills.pdf)
