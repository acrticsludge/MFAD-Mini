# IPL Power Ranking: Presentation Script

**Total time:** about 9-10 minutes | **Slides:** 15 | **Speakers:** Anubhav (1-4), Arnab (5-8), Anish Alladi (9-11), Anish De (12-15)

| Speaker | Slides | Time |
|---|---|---|
| Anubhav Rai (PES1UG25CS078) | 1-4: Welcome, data, matrix, row reduction | ~2:20 |
| Arnab Sen (PES1UG25CS093) | 5-8: rank, redundancy, orthogonalisation, projection | ~2:30 |
| Anish Alladi (PES1UG25CS070) | 9-11: least squares, eigenvector, diagonalisation | ~2:00 |
| Anish De (PES1UG25CS071) | 12-15: ranking, official table, conclusions, thank you | ~2:20 |

---

## Part 1: Anubhav (slides 1-4)

### Slide 1: Welcome (~25 s)
Good morning, ma'am. We are Anubhav, Arnab, Anish Alladi and Anish De. Our project ranks IPL franchises using only linear algebra: matrices, rank, projection and eigenvectors. We will walk through eleven steps, from raw match data to a final ranking, in about ten minutes. I will start with the data and the matrix.

### Slide 2: Stage 1, The data decides the maths (~40 s)
The dataset has 1,243 matches over 19 seasons. 25 have no winner, so we drop them, which leaves 1,218. Only 558 of those record a run margin. The other 660 were won by wickets and carry no run figure. We did not convert wickets into runs, because that would be invented data. So we build two models: Massey on the 558 run-margin matches, and Colley on all 1,218.

### Slide 3: Stage 2, One match, one equation (~40 s)
Each run-margin match becomes one equation. A has 558 rows and 15 columns, one per franchise: plus one for the winner, minus one for the loser, zero otherwise. The right-hand side b holds the run margin. We solve A x equals b for the team strengths x. Notice that every row sums to zero. That will matter in the next two steps.

### Slide 4: Stage 3, Row reduction: the pivots (~35 s)
We simplify A with Gauss-Jordan elimination, written by hand with partial pivoting. We get 14 pivot rows, and every other row reduces to zero, 544 of them. One column, Sunrisers Hyderabad, never gets a pivot. That is the free column. So A is not full rank. **Arnab will take it from here.**

---

## Part 2: Arnab (slides 5-8)

### Slide 5: Stage 4, Rank 14 of 15, nullity 1 (~40 s)
That gives rank 14 and nullity 1, out of 15 columns. The singular values confirm it: the smallest real one is 2.2, and the fifteenth is about 5 times 10 to the minus 15, fourteen orders of magnitude lower, so it is zero. The null direction is the all-ones vector, because rows sum to zero. Adding the same runs to every team changes nothing, so only differences between teams can be measured.

### Slide 6: Stage 5, Only 14 rows matter (~30 s)
Next, we remove redundancy. Of the 558 equations, only 14 are linearly independent. The other 544 are combinations of those 14 and add no new information. We keep the 14 pivot rows, taken as they are from A. That is a basis for the row space.

### Slide 7: Stage 6, Orthonormal bases (~40 s)
Now we orthogonalise, in two different spaces. The column space sits inside R to the 558. QR factorisation gives 14 orthonormal columns that span it, and a fifteenth that lies outside it. The row space sits inside R to the 15. Gram-Schmidt on the 14 pivot rows gives an orthonormal basis there, with Q times Q transpose equal to identity. We also corrected an earlier mistake of treating QR as the row-space basis.

### Slide 8: Stage 7, Projecting b onto Col(A) (~40 s)
Now we project b onto the column space. b splits into a fitted part, A x-hat, of length 142 runs, and a residual of length 963 runs. The residual is exactly perpendicular: its dot product with each of the 14 directions is zero to about 10 to the minus 13. That is the normal equations, A transpose r equals zero. And Pythagoras holds: the squared lengths 20,259 and 928,185 add up to the squared length of b. **Anish Alladi will continue.**

---

## Part 3: Anish Alladi (slides 9-11)

### Slide 9: Stage 8, Least squares: a weak fit (~40 s)
The projection gives the least-squares solution, and three different routes agree to about 5 times 10 to the minus 14. But the fit is weak. Centred R-squared is minus 0.21, and winner accuracy is 55 percent. The residual spread, 36.9 runs, is almost the whole spread of the data, 37.1, while the fitted team strengths vary by only 7 runs. So in this model, run margins carry little team signal.

### Slide 10: Stage 9, Colley: the leading eigenvector (~45 s)
Second model: Colley, on all 1,218 decided matches. We form M equals W plus W transpose plus C, where W counts wins and C counts games played. M is symmetric and non-negative, so Perron-Frobenius guarantees a positive leading eigenvector. Power iteration finds it in 9 steps: lambda 1 is 469.18, which dominates lambda 2 of 14.81 by 31.7 times. Every team's share comes out strictly positive.

### Slide 11: Stage 10, Diagonalising A-transpose A (~35 s)
Diagonalisation simplifies the problem. A transpose A is a 15 by 15 symmetric positive semi-definite matrix, replacing the 558 by 15 one. Its eigenvalues are exactly the squared singular values of A. And the single zero eigenvalue is the same rank-14 deficiency we saw in stage 4. What we found by elimination shows up again here. **Anish De will finish.**

---

## Part 4: Anish De (slides 12-15)

### Slide 12: Stage 11, Ranking with both models (~45 s)
Now the final output. On the left, Massey: every one of the 15 coefficients lies within two standard errors of zero, the largest t-value is only 1.2. The most extreme ones, Kochi and Gujarat Lions, come from just 5 matches each. On the right, Colley gives all-positive shares, with Mumbai, Bangalore, Kolkata and Delhi on top.

### Slide 13: Stage 11, Checking the official table (~35 s)
We compare both rankings with the official points table, joined by team name. Colley agrees strongly, Spearman 0.94. Massey barely agrees, 0.09, and it has no agreement with Colley at all. So win-and-loss information ranks the teams sensibly, while our run-margin least squares does not.

### Slide 14: Conclusions and limits (~40 s)
To conclude: rank, null space, projection and eigenvectors all behaved as the theory predicts. One limitation we found in our own audit: in the design matrix, 123 of the 558 rows have an inconsistent sign. Re-fitting with consistent signs lifts the Massey versus official Spearman from 0.09 to 0.60. So the Massey figures are provisional, while the structural results, rank and null space, stand.

### Slide 15: Thank you (~20 s)
That is our work. To recap: the data became a matrix, elimination found rank 14, projection gave least squares, and the eigenvector gave a robust ranking. Thank you, ma'am. We are happy to take questions.

---

## Likely questions

- **Why not convert wicket margins to runs?** It would need an invented conversion factor, so we kept two models on two datasets.
- **Why is there a null space?** Every row has one +1 and one -1, so rows sum to zero. Adding a constant to all strengths changes no prediction.
- **Is the "official table" the real IPL table?** No. It is computed from our snapshot at 2 points per win across all 19 seasons, and the 25 no-winner matches are excluded.
- **What about the sign issue?** The design-matrix sign convention is inconsistent in 123 of 558 rows. A re-fit with consistent signs gave Massey vs official 0.60. Rank and null space are structural and unaffected.
