# Kraken Acquisition Design Review

## Status

Architecture review complete.

No acquisition configuration was changed during this review.

## Purpose

Determine whether the existing 25 kS/s Kraken IQ recordings preserve the
available synchronized RF information sufficiently for continued
device-discrimination research, and identify the boundary at which a future
wider-IQ experiment would need to operate.

## Established acquisition path

The inspected Kraken/HeIMDALL implementation establishes the following path:

1. RTL-SDR acquisition operates at 2.4 MS/s.
2. The HeIMDALL firmware decimation ratio is currently 1.
3. Rebuffered data is converted into complex float32 / NumPy complex64
   representation without active rate reduction at the firmware decimator.
4. `delay_sync` produces synchronized multichannel IQ through the
   `delay_sync_iq_A/B` shared-memory interface.
5. The Kraken receiver consumes this synchronized IQ through
   `inShmemIface`.
6. Global DSP decimation is currently 1.
7. The configured VFO bandwidth is 25,000 Hz.
8. The VFO channelizer calculates an integer decimation factor from the
   input sampling frequency and VFO bandwidth.
9. At 2.4 MS/s and 25 kHz, the factor is 96:
      2,400,000 / 96 = 25,000 complex samples/s.
10. The VFO channelizer applies frequency-selective filtering, decimation,
    and frequency translation.
11. The resulting VFO IQ is accumulated and written to `records/iq/*.iq`.

Therefore the IQ files used by the existing feature experiments are a
channelized 25 kS/s representation derived from the synchronized
2.4 MS/s stream.

## Shared-memory safety finding

`delay_sync_iq` is not a passive broadcast interface.

The implementation uses:

- shared-memory buffers A/B,
- a forward FIFO carrying buffer-ready notifications,
- a backward FIFO carrying buffer-free acknowledgements.

The receiver consumes a ready notification, copies the corresponding IQ
frame, and acknowledges that buffer to the producer.

A second independent consumer of the same FIFO pair could compete for
notifications and acknowledgements. It must therefore not be treated as a
safe passive tap.

## IQ server finding

The HeIMDALL source contains `iq_server.out`, which can expose IQ through
TCP port 5000.

However, the IQ server itself consumes the same `delay_sync_iq` shared-memory
interface and participates in the same buffer-ready/buffer-free handshake.

It is therefore not considered a safe parallel fan-out mechanism alongside
the current SHM Kraken receiver.

At the time of this review no live TCP port 5000 listener or `iq_server`
process was present.

## Frozen baseline

The existing experimental baseline remains unchanged:

- VFO frequency: 433.868160 MHz
- VFO bandwidth: 25 kHz
- VFO IQ recording: enabled
- squelch mode: Manual
- squelch threshold: -45 dB
- global DSP decimation: 1
- firmware decimation ratio: 1

Existing captures and analyses remain evidence for this acquisition
representation only.

## Research interpretation

Episode Features V1, Episode Features V2, and Waveform Structure V1 all
operate on the same 25 kS/s channelized representation.

Those analyses did not establish a feature suitable for advancing the
S1/S2 discrimination result to the reserved S3 validation stage.

This does not demonstrate that wider-band IQ will discriminate devices.

It does establish a justified acquisition-design question:

> Does a wider synchronized RF representation preserve useful
> device-dependent structure that is absent or insufficiently represented
> after the current 25 kS/s VFO channelization?

This question must be tested prospectively rather than assumed.

## Safety constraints for future work

Do not:

- start a second `rtl_sdr` process while Kraken owns the tuners;
- attach another `inShmemIface` consumer to the live `delay_sync_iq` FIFO;
- launch `iq_server.out` in parallel with the existing SHM consumer without
  redesigning and validating the data path;
- modify the working Kraken installation merely to obtain experimental data;
- alter the frozen 25 kS/s baseline and retrospectively compare it as though
  acquisition conditions were unchanged.

## Next stage

Design a separate, pre-registered wider-IQ acquisition experiment.

The experiment should define before collection:

- acquisition representation;
- sample rate / usable bandwidth;
- sensor allocation;
- controlled geometry;
- activation count;
- provenance requirements;
- primary comparison;
- advancement rule;
- failure / inconclusive criteria.

No claim is made in advance that wider bandwidth will improve
device discrimination.
