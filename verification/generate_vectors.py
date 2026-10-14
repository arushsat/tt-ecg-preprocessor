"""Independent integer/queue model; emits before/after-edge expectations."""
import random
from pathlib import Path


def generate():
    rng = random.Random(20261014)
    history = [0, 0, 0]
    pending = None
    result = 0
    rows = []
    accepted = consumed = resets = 0

    def cycle(sample=0, valid=0, ready=1, reset_n=1, enable=1):
        nonlocal history, pending, result, accepted, consumed, resets
        can_accept = int(bool(reset_n and enable and (pending is None or ready)))
        has_output = int(bool(reset_n and enable and pending is not None))
        before_result = result
        if not reset_n:
            history, pending, result = [0, 0, 0], None, 0
            resets += 1
        elif enable:
            if has_output and ready:
                consumed += 1
                pending = None
            if valid and can_accept:
                window = history + [sample]
                result = sum(window) // 4  # Python floors negative results.
                assert -128 <= result <= 127
                history = window[1:]
                pending = result
                accepted += 1
        after_ready = int(bool(reset_n and enable and (pending is None or ready)))
        after_valid = int(bool(reset_n and enable and pending is not None))
        rows.append((reset_n, enable, sample & 255, valid, ready,
                     can_accept, has_output, before_result & 255,
                     after_ready, after_valid, result & 255))

    cycle(reset_n=0)
    cycle()
    # Startup, impulse, positive/negative extrema, constant values and rounding.
    for stream in ([100,0,0,0,0], [-1]*8, [-128]*8, [127]*8,
                   [-128,127]*8, [1,2,3,4,5,-1,-2,-3,-4]):
        cycle(reset_n=0)
        for x in stream:
            cycle(x, valid=1)
        cycle()
    # Every 8-bit input held for four accepted samples reaches that exact value.
    for x in range(-128,128):
        for _ in range(4):
            cycle(x, valid=1)
        assert result == x
    # A full output register, long stall, disable/re-enable, simultaneous transfer.
    cycle(80, valid=1)
    for _ in range(20):
        cycle(-72, valid=1, ready=0)
    for _ in range(5):
        cycle(-72, valid=1, ready=1, enable=0)
    cycle(-72, valid=1)
    cycle(reset_n=0, enable=0)
    # Protocol-compliant producer: keeps valid/data until a transfer or reset.
    held = None
    for _ in range(10000):
        reset_n = int(rng.randrange(100) != 0)
        enable = int(rng.randrange(10) != 0)
        ready = int(rng.randrange(3) != 0)
        if held is None and rng.randrange(4):
            held = rng.randrange(-128,128)
        cycle(held if held is not None else 0, int(held is not None),
              ready, reset_n, enable)
        if not reset_n or (held is not None and rows[-1][5]):
            held = None
    cycle()
    cycle()
    dest = Path(__file__).with_name('vectors.txt')
    dest.write_text(''.join(' '.join(map(str,row))+'\n' for row in rows))
    print(f'Model generated {len(rows)} cycles; {accepted} inputs, '
          f'{consumed} outputs, {resets} reset cycles. RTL execution still required.')

if __name__ == '__main__':
    generate()
