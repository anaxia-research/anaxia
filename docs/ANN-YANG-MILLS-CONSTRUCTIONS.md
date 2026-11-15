# Two constructions for the weak-coupling pressure estimate

The replica identity compares the Wilson partition functions on one fixed link space at the same coupling. A second approach works directly with the normalized transfer operator. Both specify estimates whose constants must survive the weak-coupling limit. [Replica identity](ANN-YANG-MILLS-REPLICA-SEAMS.md) · [One-scale criterion](YANG-MILLS-ONE-SCALE.md)

## Connected activities on a single doubled graph

Let \(P\) be the finite list of plaquette terms in the doubled Wilson model, including both matchings at each cut. For \(X\subset P\) let \(Z_X\) be the normalized Haar integral with only terms in \(X\) active. Put

\[
A_Y = \sum_{X\subset Y}(-1)^{|Y|-|X|}\log Z_X.
\]

Möbius inversion gives \(\log Z_P=\sum_Y A_Y\). If \(Y\) splits into two nonempty parts with disjoint link variables, every \(Z_X\) factors into the corresponding integrals. The alternating sum of each of the two resulting log terms is zero. Thus only connected activities survive, with adjacency given by sharing a link. An activity depends on the interpolation parameters only through its active plaquette terms.

Let \(\square F=F(1,1)-F(1,0)-F(0,1)+F(0,0)\). Every activity that depends on only one cut cancels, as does every activity independent of the cuts. The exact sum \(2\Psi=\square F\) therefore involves only activities reaching both cuts. No pairing of coefficients from independent blocking procedures on \(T\) and \(2T\) is needed.

For a quantitative implication, suppose a blocked expansion on this one graph preserves this seam locality. At scale \(\ell\le T\) assume that the sum over activities rooted at each coarse cell of
\(e^{\kappa\operatorname{diam}_t(X)/\ell}\sup_{u,v}|A_X(u,v)|\)
is at most \(K_\ell\). Each surviving activity spans cyclic fine-time distance at least \(d-1\), where \(d=\lfloor T/2\rfloor\). It meets at most four possible time layers of anchors at cut \(a\), counting both sheets. There are at most
\(4\prod_i\lceil s_i/\ell\rceil\le(27/2)V/\ell^3\)
such anchors because \(s_i\ge2T\). Multiplying by four for the absolute corner sum and dividing by two for \(\Psi\) gives

\[
\frac{T^3|\Psi|}{V}
\le 27\sum_\ell K_\ell (T/\ell)^3 e^{-\kappa(d-1)/\ell}
    +\frac{T^3|\square R|}{2V},
\]

where \(R\) is the terminal remainder. The same count includes short boundary blocks. If \(T\ge6\), then \(d-1\ge T/4\). For dyadic scales \(\ell\le T/L\) with \(K_\ell\le K\) and \(L\ge12/\kappa\), the successive finer-scale contributions have ratio at most \(8e^{-\kappa L/4}<1/2\). Their total is at most \(54K L^3 e^{-\kappa L/4}\). The outstanding Wilson estimates are the uniform activity norm on the doubled graph and a small mixed terminal remainder, including the large-field contributions.

Exact cancellation alone supplies no such norm. In a normalized Ising ring of length \(L\) and bond coupling \(J\), every proper bond subset is a forest and has partition function \((\cosh J)^{|X|}\). The full ring has the extra factor \(1+\tanh(J)^L\). Its winding activity tends to \(\log 2\) as \(L e^{-2J}\to0\). The ann worker checks the same cancellation on a rational four-edge ring without floating-point logarithms.

## Blockwise control of the transfer trace

Let \(R\) be the Wilson transfer operator divided by its top eigenvalue. With its normalized positive vacuum vector \(h\), the conjugate \(P=h^{-1}Rh\) is a reversible Markov operator with stationary measure \(\pi=h^2d\mu\). For an integer \(t\), let \(p_t\) denote the density of \(P^t\) against \(\pi\). By reversibility,

\[
Z_{\rm vac}(2t)=\operatorname{Tr}R^{2t}
               =\int p_t(x,y)^2\,d\pi(x)d\pi(y).
\]

Split the terminal configuration \(y\) into blocks \(Y_1,\ldots,Y_k\). The density ratio factors into the conditional ratios \(\ell_j\), comparing the law of \(Y_j\) given \(X,Y_{<j}\) with its stationary conditional law given \(Y_{<j}\). Under the independent product measure put
\(S_j=\mathbb{E}\prod_{i\le j}\ell_i^2\), with \(S_0=1\).
Conditional integration gives

\[
\log Z_{\rm vac}(2t)
=\sum_{j=1}^k\log\bigl(1+\mathbb{E}_{\theta_{j-1}}\chi_j^2\bigr),
\]

where \(\chi_j^2\) is the conditional chi-square divergence and
\(\theta_{j-1}\) has density \(\prod_{i<j}\ell_i^2/S_{j-1}\) on the revealed histories. This tilt specifies the histories whose contribution has to be controlled.

At \(T=2t\), take block sides at most \(b\le t\). The number of blocks is at most \((125/64)V/b^3\). If each tilted mean is at most \(C e^{-mt/b}\), then

\[
\frac{T^3}{V}\log Z_{\rm vac}(T)\le
\frac{125}{64}C(T/b)^3e^{-mT/(2b)}.
\]

A sufficiently small right-hand side supplies the pressure seed directly. For example, a conditional likelihood ratio of form \(e^g/\mathbb{E}e^g\) with oscillation at most \(q\) has \(\chi^2\le\sinh^2(q/2)\). To see this, write \(e^g\in[A,B]\), use \(z^2\le(A+B)z-AB\), and maximize the resulting bound on \(\mathbb{E}z^2/(\mathbb{E}z)^2\). Thus one concrete target is a Wilson conditional log-likelihood estimate uniform in the cutoff, on blocks at the physical scale and under the revealed prefixes.

A physical gap alone does not bound the trace at this scale. For \(V\) independent spins with Hamiltonian \((\kappa/T)\sum_i(I-E_i)\), where \(E_i\) refreshes spin \(i\), the gap is \(\kappa/T\). Yet \(Z_{\rm vac}(T)=(1+e^{-\kappa})^V\), so pressure per site is independent of \(T\). This control isolates state multiplicity. The ann worker replays the conditional trace identity on exact rational transfer matrices. The uniform Wilson conditional bound remains open.
