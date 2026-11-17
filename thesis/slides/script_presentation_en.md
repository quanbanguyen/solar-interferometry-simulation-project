# Thesis Defense Presentation Script

**Title:** End-to-End Simulation of a Four-Element UHF Radio Interferometer for Solar Radio Observation at 610 MHz
**Main content duration:** ~12 minutes (14 content slides + title + outline)
**Backup duration:** not timed — used only if asked

> How to use this: each section below corresponds to exactly one slide in `slides.pdf`, numbered as shown in the top-left corner of that slide (e.g. "1.1", "2.2"...). The time in parentheses is an estimate for that slide — the main content totals ~730 seconds (~12 minutes 10 seconds), with a little slack for slide transitions and breathing room. *Italic* notes are instructions for you (do not read them aloud); everything else is spoken text — read it naturally rather than memorizing it word for word.

---

## Opening (before slide 1, ~15s)

Good morning/afternoon to the members of the committee. I would like to present my graduation thesis, titled **"End-to-End Simulation of a Four-Element UHF Radio Interferometer for Solar Radio Observation at 610 MHz."** My name is Nguyen Ba Quan, student ID 20224350, supervised by Assoc. Prof. Dr. Ha Duyen Trung. I will now begin my presentation.

## Slide "Outline" (~10s)

My presentation has seven parts: motivation, method, antenna hardware and setup, validation, results on optimizing antenna placement, diagnosis of the earlier field-trial failure, and finally conclusions and future work.

---

## 1.1 — Motivation: Why Monitor Solar Radio Bursts (~50s)

First, the motivation. Solar flares and coronal mass ejections produce solar radio bursts. These bursts change the electron density of the ionosphere, which in turn disturbs electronic devices that depend on satellite signals. A concrete example: in 2022, a geomagnetic storm caused SpaceX to lose 38 of 49 newly launched Starlink satellites. Ground-based radio observation can give one to three days of early warning before these effects reach the ionosphere. It's also worth noting that Type II and Type III bursts can raise the flux by four to five orders of magnitude above the quiet-Sun background — I have a detailed burst classification in the backup slides if the committee would like more detail.

## 1.2 — Big Dish vs. Aperture Synthesis (~55s)

So how do we observe this? There are two approaches. On the left is a single large dish, such as FAST in China, 500 meters in diameter — resolution scales with dish diameter, but this is close to a physical construction limit, and the cost runs into hundreds of millions of dollars. On the right is aperture synthesis, as used by the DLITE array in the US — resolution here does not depend on the size of any single antenna, but on the longest **baseline**, the largest distance between any two antennas. Cost is only a few thousand dollars per antenna, and the array can be expanded simply by moving or adding antennas. But as the table below shows, the price paid is that all the complexity shifts from mechanical structure to signal processing: signals from multiple antennas must be combined phase-coherently. This is exactly the problem this thesis simulates and validates.

## 1.3 — Objectives (~50s)

Before moving to the method, let me give the direct motivation for this thesis. In an earlier field deployment at Xuan Mai, using 2 Yagi-Uda antennas 8 meters apart, the result was only an ambiguous day/night trend — no clear interference fringes were observed, and there was no way to diagnose where the fault lay in the hardware chain just by inspection. This thesis builds and validates an end-to-end simulation, then uses that simulation to **diagnose the exact cause** of that failure — with quantified numbers and a concrete hardware fix, which I will present in the results. From that context, the thesis sets two objectives: first, to build a trustworthy physics simulation, from signal through the correlator to image, validated against classical theory and real hardware; second, to use that simulator to optimize antenna placement in space, finding the layout that gives the best 2-D resolution using the same antennas, without buying more hardware.

---

## 2.1 — Simulation Pipeline: From Flux to Image (~55s)

Here is the full simulation pipeline, in three stages. Stage one, generate signal: real 610 MHz solar flux combined with the antenna pattern simulated in 4NEC2, through the Friis equation, plus Johnson–Nyquist thermal noise, produces a voltage at each antenna. Stage two, correlate: cross-multiply and time-average every antenna pair to produce a visibility. Stage three, image: using the (u,v,w) geometry and an inverse Fourier transform to produce a dirty image and its PSF. This same three-stage chain is re-run for every candidate antenna layout — comparing those outputs is the second half of the thesis.

## 2.2 — What Is a Visibility? (~70s)

This slide explains the core concept of interferometry: what a visibility actually is. Consider two antennas separated by a baseline b. A plane wave arriving from the source at angle θ from zenith reaches antenna 2 slightly earlier than antenna 1, by a geometric delay τ, equal to b times sine θ, divided by the speed of light. The correlator multiplies the two voltages V1 and V2 and time-averages them, producing **a single complex number** — that is the visibility, corresponding to one interference fringe on the sky. As the Earth rotates, the angle θ changes throughout the day, so the correlator output oscillates — that is the measurable **fringe**. Mathematically, each baseline corresponds to one spatial frequency; many different baselines give many different Fourier components, which combine to reconstruct an image of the sky — this is the van Cittert–Zernike theorem.

---

## 3.1 — Antenna: A Validated Model (~50s)

Moving to hardware. The antenna used is a commercial HKD G11KD-T2 Yagi-Uda, modeled wire-by-wire in 4NEC2. The table on the left shows the main simulated parameters: input impedance, gain, half-power beamwidth, and SWR. The table on the right is the key point: I cross-checked the 4NEC2 simulation against **direct NanoVNA measurement** — measured SWR of 1.59 versus simulated 1.55, a very small discrepancy. This confirms the simulated antenna model is trustworthy enough to drive the entire imaging pipeline. I also studied mutual coupling between antennas — coupling falls below −78 dB at 5 meters, and −87 dB at 10 meters, meaning that at every operating baseline used in this thesis, 8 meters and above, the antennas behave **independently**, exactly matching the underlying assumption of aperture-synthesis theory.

## 3.2 — Real Input Data (~35s)

The input to the entire simulation is real, already-calibrated 610 MHz flux from the SWS Learmonth observatory in Australia, dated 20 March 2025 — this is not synthetic data, it's a real measurement. The main parameters: frequency 610 MHz, bandwidth 1 MHz, an ideal system temperature of 150 K, a site latitude of −22.2 degrees, and baselines swept from 8 to 130 meters, using the same 4-antenna hardware throughout.

---

## 4.1 — Visibility Validation: Fringe & Jinc Curve (~55s)

This is the validation section — critical for proving the simulation is trustworthy. On the left: on the 8-meter adjacent-pair baseline from Case 1, the correlator output oscillates with a period of about 14 minutes, matching the analytic prediction for that exact baseline and date. On the right: the visibility amplitude falls off with baseline length, landing exactly on the analytic jinc curve for a uniform solar disk, with the first null at about 130 wavelengths. These two independent checks, both satisfied on real solar flux, confirm that the correlator correctly implements the van Cittert–Zernike theorem.

## 4.2 — Imaging Validation: Dirty Image = Sky * PSF (~45s)

A third check, this time in the imaging domain: (a) is the true sky model — a simulated disk representing the Sun; convolved with (b), the point-spread function, the result must equal (c), the dirty image computed directly from the data via gridding and FFT. These two independent computation paths — convolution versus direct computation — agree to **machine precision**. This confirms that the correlator, the (u,v)-sampling, and the inverse Fourier transform are all self-consistent, for any 2-D array layout.

---

## 5.1 — Why Array Layout Matters (~45s)

With the simulator validated, I used it to answer the second question: what is the best way to arrange the antennas. Comparing two layouts: a compact East-West layout gives only 1-D (u,v) coverage, so the PSF is stretched into a single elongated stripe — the image is blurred in the North-South direction. A graded-cross layout, spread in both directions, fills the (u,v) plane two-dimensionally, so the PSF sidelobes drop by about 20 dB compared to the compact layout. The key point: it's the 2-D coverage itself that removes the sidelobes — the placement study on the next slide isolates exactly this effect, with a fixed 4-antenna budget.

## 5.2 — Array Geometry Comparison (~60s)

This is the most important results table in the thesis. I kept the same 4 antennas throughout, only changing the layout. Case 1, a 24-meter East-West line: North-South resolution is only 180 arcminutes — essentially unresolved in that direction. Case 1.5, adding a North-South arm to form a cross: improves to 62.1 arcminutes, 2.9 times better. Case 1.75, a DLITE-inspired triangle-plus-center layout, so that all 6 baselines point in distinct directions: resolution reaches 19.8 arcminutes — **9.1 times better** than Case 1. The key point I want to emphasize: across all three cases, the hardware never changed — rearrangement alone improved resolution by more than a factor of 9.

*(Note: if asked about a 130-meter extended array — that's a separate 17-element design, not the same 4-antenna hardware; see backup slide 8.9.)*

## 5.3 — Sensitivity and Burst Detectability (~35s)

On sensitivity: the minimum detectable flux is about 0.026 to 0.183 solar flux units, depending on how many integration dumps are averaged. The quiet-Sun detection SNR exceeds 500 to 1 across every configuration tested. And most importantly for the science goal: Type II and Type III bursts exceed the noise floor by four to five orders of magnitude — meaning the system is fully capable of detecting real burst events.

---

## 6.1 — Closing the Loop: Diagnosing the Field Trial (~55s)

Now, back to the opening question: why did the Xuan Mai field trial fail? By comparing the simulator against a real 2-antenna measurement from the same day, 20 March 2025, I isolated **two specific, quantifiable causes**. First, an uncalibrated receiver chain: the measured solar excess was 23.8 times below the simulated prediction, corresponding to an effective system temperature of about 3600 K, instead of the assumed 150 K — meaning the LNA chain was never calibrated in the field. Second, clock incoherence: a typical RTL-SDR crystal drifts by about 1 part per million, giving a coherence time of only about 1.6 milliseconds at 610 MHz — four orders of magnitude shorter than the 43.2-second dump — causing the fringe amplitude to collapse to zero regardless of how good the SNR is. The key conclusion: the field failure was **not a concept failure** — it reduces to two specific, fixable hardware requirements: calibrate the system temperature, and add a GPS-disciplined clock or a shared 10 MHz reference.

## 7.1 — Conclusion & Future Work (~45s)

In summary, both original objectives were achieved. First, a trustworthy physics simulator: the antenna model was cross-checked directly against NanoVNA measurement, mutual coupling confirms the antennas behave independently, and the simulated visibility, fringe, and imaging all match analytic theory on real solar flux data. Second, optimized antenna placement: with the same 4 antennas, rearranging from a line to a DLITE-style triangle gives a 9.1 times improvement in North-South resolution. For future work: build a hardware correlator on an FPGA and validate fringes hardware-in-the-loop; upgrade the physical Xuan Mai deployment to the triangle-plus-center layout, with a calibrated LNA chain and a GPS-disciplined clock; and record real Type II/III burst events, incorporating CLEAN deconvolution, toward real-time operation.

**Thank you for your attention. I am ready to answer the committee's questions.**

---
---

# BACKUP SECTION — present only if asked

*The slides below are not part of the timed 12 minutes. When a question comes up, switch to the matching backup slide and use the short script below as a starting frame — answer naturally based on the actual question, rather than reading verbatim.*

## 8.1 — Backup: Key Contributions

*Use when asked "what are the main contributions of this thesis."*

The thesis has five main contributions. First, a validated antenna model, cross-checked by direct NanoVNA measurement, plus a mutual coupling study proving the elements behave independently at every operating baseline. Second, a general end-to-end interferometry engine, using one consistent (u,v,w) formulation for per-antenna phase, baseline projection, and fringe stopping — applicable to any 2-D array layout. Third, validation with real data: the pipeline runs on real Learmonth flux and reproduces three classical aperture-synthesis signatures simultaneously. Fourth, a structured comparison against the APSYNSIM teaching tool, with four concrete advantages: real data, a real antenna beam, physics-based noise, and a path toward FPGA hardware. Fifth, a single reproducible workflow, from a raw flux file to a calibrated dirty image in under two minutes of computation.

## 8.2 — Backup: Solar Radio Bursts, Types I–V

*Use when asked to distinguish burst types.*

Solar radio bursts are classified into five types based on their dynamic spectral signature. Type I is long-lived, narrowband noise storms. Type II drifts slowly, tracing the shock front of a CME propagating through the corona. Type III drifts very rapidly, caused by electron beams on open field lines, and dominates at decimetre wavelengths — this is the band most relevant to this thesis. Type IV is broadband continuum following a flare. Type V is brief continuum sometimes following Type III, tracing trapped electron streams. The simulation's parameter table includes Type II, III, IV, and the quiet-Sun case.

## 8.3 — Backup: The Idea of Interferometry, Step by Step

*Use for an intuitive, non-specialist explanation of how interferometry works.*

This is a step-by-step illustration of the interferometry concept. With two antennas and the source dead ahead, there is no time lag. When the source moves off to one side, a small time lag appears between the antennas. A real source is not a single point, so more antennas are needed. With just three antennas, the reconstructed image is only a coarse, striped pattern. With 30 antennas, the true shape becomes clear. The core idea: each antenna pair measures one time lag, corresponding to one piece of the picture — more antennas, more pairs, and a sharper image.

## 8.4 — Backup: 3-D Radiation Pattern & E-plane

*Use if asked in more depth about the antenna's radiation pattern.*

This is the full simulated radiation pattern from 4NEC2. On the left is the E-plane, the vertical cross-section; on the right is the full 3-D directivity pattern at 610 MHz. The antenna has strong gain toward the horizon, which matches well with the Sun's low elevation angle at the Learmonth site's latitude for most of the observing window.

## 8.5 — Backup: Full Input & Voltage Synthesis

*Use if asked for detail on the flux-to-voltage conversion step.*

This is the complete input signal chain. The top plot is the real, already-calibrated 610 MHz flux taken directly from SWS Learmonth — raw input, not re-simulated. The bottom plot is that same track after being passed through the Friis equation, multiplied by the 4NEC2 main-beam pattern, and with noise added — giving the per-antenna complex baseband voltage, ready for correlation.

## 8.6 — Backup: Array Geometry, Site & Observing Setup

*Use if asked about the site's geometric setup.*

The Learmonth observing site has a latitude of −22.2 degrees; the Sun transits within an hour angle range of ±90 degrees, a 12-hour observing window. Each antenna's East-North-Up ground position is rotated first by the site latitude, then by the Sun's current hour angle and declination, to give every baseline's (u,v,w) coordinates, in wavelengths, at every instant.

## 8.7 — Backup: Mutual Coupling Curve

*Use if asked in depth about coupling effects between antennas.*

On the left, measured and simulated coupling |S21| versus baseline distance: the circles are simulation in the measurable 0.5–3 meter range, and the red crosses are direct simulation at 5, 10, and 15 meters. Coupling falls below −78 dB by 5 meters, and −87 dB by 10 meters. On the right, the practical consequence: the impedance distortion that coupling causes on each active element — already under 0.02% by 5 meters. Both views agree: at the operating baselines used in this thesis, 8 meters and above, the antennas behave independently, with no need for Jones-matrix cross-coupling correction.

## 8.8 — Backup: Position Matrix — Computing (u,v,w)

*Use if specifically asked "how do you compute the (u,v,w) coordinates" — this is the most likely math question.*

Computing (u,v,w) involves two successive coordinate rotations. Step one: from the local East-North-Up frame to the equatorial X, Y, Z frame, by rotating through the site latitude φ — this matrix is fixed, it does not change over time. Step two: from the equatorial frame to the baseline frame u, v, w, by rotating through the source's hour angle H and declination δ — this matrix is time-varying, since the Sun moves across the sky. These same two matrices are reused throughout the simulation: for per-antenna phase in the signal-generation stage, and for the baseline coordinates of every antenna pair in the imaging stage. As the hour angle H changes over the course of the day, each baseline traces out an arc in the (u,v) plane — this is the mechanism of Earth-rotation synthesis.

## 8.9 — Backup: Beyond 4 Antennas (Case 2)

*Use if asked about the 130-meter array/Case 2, or specifically if asked "is Case 2 the same 4 antennas" — the honest answer is NO.*

Unlike Cases 1/1.5/1.75, this is not the same 4-antenna hardware — it's a separate design, a 17-element 2-D graded cross: one center antenna plus 4 arms, each with antennas at radii of 5, 15, 35, and 65 meters. This case uses the idealized forward model — a uniform, noise-free solar disk — rather than real SFU flux data. With baselines out to 130 meters, about 264 wavelengths at 610 MHz, this goes past the roughly 132-wavelength visibility null discussed in the validation section, so East-West resolution reaches about 11 arcminutes, beginning to resolve the 32-arcminute disk. This is a separate design question: if more antennas become available in the future, a graded 2-D array like this is the direction to start resolving the shape of the solar disk itself, not merely detecting it.

## 8.10 — Backup: Full Array Sweep (5 Layouts)

*Use if asked about the broader sweep beyond the 3 main cases.*

This is the full sweep across five candidate layouts: compact East-West, linear, a T-shape, an extended two-dimensional graded cross, and a random layout. The top row is the dirty image, the middle row is the PSF, and the bottom row is the (u,v) coverage. The pattern is clear: the more evenly a layout fills the (u,v) plane in all directions, the tighter the PSF and the lower its sidelobes. Note: the linear/tee/extended/random layouts in this sweep use different antenna counts, not the same 4 antennas as the main results table.

## 8.11 — Backup: Sensitivity Detail

*Use if asked in depth about the noise budget or exporting data to FPGA hardware.*

A few more details on sensitivity. Quiet-Sun SNR exceeds 500 to 1 across every configuration, rising to about 1700 to 1 when averaging 50 dumps. On a single sample, SNR is only about −3.8 dB — the signal is genuinely buried in noise sample-by-sample — but after averaging within one dump, SNR recovers to about 13 to 1, exactly the behavior expected of a real radio telescope. On the hardware side: the noise floor occupies more than 20 LSBs of a 16-bit sample, meaning the signal is ready to be exported to an FPGA hardware correlator without risk of overflow or insufficient resolution.
