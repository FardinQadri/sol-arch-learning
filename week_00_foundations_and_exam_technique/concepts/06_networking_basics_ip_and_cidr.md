Exam tasks: 3.4

# 06 — Networking basics: IP addresses, CIDR and subnets

## What it is

A primer for people who have never done networking. It covers what an IP
address is, what `10.0.5.0/24` means, how to tell whether an address is inside
a block, and why an AWS subnet holds fewer machines than you expect. Week 02
(VPC) builds on every line of this. If you already know CIDR, skim the
self-check and move on.

You never need binary here. Everything is done by comparing numbers.

## How it works

### 1. An IP address is 4 numbers

```
10.0.5.20
```

An IP address is **4 numbers separated by dots**. Each number is between
**0 and 255**. Think of it as a phone number for a computer.

### 2. A network owns a group of addresses

A network, such as an office or an AWS subnet, does not have one address. It
owns a **group** of them, one per machine. Listing them all is painful:

```
10.0.5.0, 10.0.5.1, 10.0.5.2, ... all the way to 10.0.5.255
```

So we write the group in a short form called **CIDR** (say "cider"):

```
10.0.5.0/24
```

### 3. The slash says how many numbers are fixed

**Divide the slash by 8.** The answer is how many numbers, from the left, are
**fixed**. The rest can be **anything from 0 to 255**. Write "anything" as `*`.

| Written as | Slash ÷ 8 | Fixed | What it really means |
|---|---|---|---|
| `10.0.0.0/8` | 1 | `10` | `10.*.*.*` |
| `10.0.0.0/16` | 2 | `10.0` | `10.0.*.*` |
| `10.0.5.0/24` | 3 | `10.0.5` | `10.0.5.*` |
| `10.0.5.20/32` | 4 | `10.0.5.20` | only `10.0.5.20` |

The `.0` placeholders after the fixed part just mean `*`. So when you see
`10.0.5.0/24`, read it as **`10.0.5.*`** first, always.

(Why 8? Under the hood each number is 8 bits and the slash counts bits. You do
not need bits to do any of the maths in this course.)

### 4. Is this address inside this block?

Translate the block to a pattern, then compare **one number at a time, from
the left**.

Is `10.0.5.20` inside `10.0.5.0/24`? The pattern is `10.0.5.*`.

```
pattern:   10  .  0  .  5  .  *
address:   10  .  0  .  5  .  20
           ✔      ✔     ✔     ✔ (* allows anything)
```

Every position matches, so **inside**.

Is `10.0.6.1` inside `10.0.5.0/24`?

```
pattern:   10  .  0  .  5  .  *
address:   10  .  0  .  6  .  1
           ✔      ✔     ✘ ← 6 is not 5. Stop.
```

One fixed number does not match, so **outside**. The last number does not
matter once something has failed. It is like a phone area code: `10.0.5.*` is
"every number with area code 10.0.5", and `10.0.6.1` has a different area code.

The same idea with /16. `10.0.0.0/16` is `10.0.*.*`, so only the first two
numbers are checked:

| Address | First two | Inside `10.0.*.*`? |
|---|---|---|
| `10.0.5.20` | 10.0 | yes |
| `10.0.99.3` | 10.0 | yes |
| `10.0.6.1` | 10.0 | yes. Outside the /24 above, inside this bigger /16 |
| `10.1.5.20` | 10.**1** | no |

### 5. How many addresses are in a block?

Each `*` can be 256 values, so multiply 256 once per star.

| Pattern | Stars | Addresses |
|---|---|---|
| `10.0.5.20` (/32) | 0 | 1 |
| `10.0.5.*` (/24) | 1 | 256 |
| `10.0.*.*` (/16) | 2 | 256 × 256 = 65,536 |
| `10.*.*.*` (/8) | 3 | about 16.7 million |

That gives the rule that feels backwards at first: **a bigger slash fixes more
numbers, so it leaves fewer stars, so the block is smaller.** A /24 is smaller
than a /16.

### 6. Slashes that do not divide by 8: cut into chunks

From /25 to /32, the first three numbers are fixed as with a /24, and the last
number is **cut into equal chunks**. A block is exactly one chunk.

Start at 256 and halve once for every step past 24:

| Slash | Chunk size | Chunks in 0–255 |
|---|---|---|
| /24 | 256 | 1 |
| /25 | 128 | 2 |
| /26 | **64** | 4 |
| /27 | 32 | 8 |
| /28 | **16** | 16 |

**/26: chunks of 64.**

```
| 0 – 63 | 64 – 127 | 128 – 191 | 192 – 255 |
```

The last number in the block tells you **which chunk** it is:

| Block | Chunk | Covers |
|---|---|---|
| `10.0.5.0/26` | 1st | `10.0.5.0` – `10.0.5.63` |
| `10.0.5.64/26` | 2nd | `10.0.5.64` – `10.0.5.127` |
| `10.0.5.128/26` | 3rd | `10.0.5.128` – `10.0.5.191` |
| `10.0.5.192/26` | 4th | `10.0.5.192` – `10.0.5.255` |

**Where a block ends = start + chunk size − 1.** For `10.0.5.64/26`:
64 + 64 − 1 = 127.

**/28: chunks of 16.**

```
| 0–15 | 16–31 | 32–47 | 48–63 | 64–79 | ... | 240–255 |
```

Sixteen small chunks, starting at 0, 16, 32, 48 and so on.
`10.0.5.16/28` covers `.16` to `.31`.

**Is it inside? Two checks.**

1. Do the **first three numbers match exactly**? (Same check as section 4.)
2. Is the **last number inside the chunk**?

| Question | Check 1 | Check 2 | Answer |
|---|---|---|---|
| `10.0.5.100` in `10.0.5.64/26`? | ✔ 10.0.5 | ✔ 100 is in 64–127 | inside |
| `10.0.5.130` in `10.0.5.64/26`? | ✔ 10.0.5 | ✘ 130 is past 127 | outside (it is in `.128/26`) |
| `10.0.5.20` in `10.0.5.16/28`? | ✔ 10.0.5 | ✔ 20 is in 16–31 | inside |
| `10.0.5.40` in `10.0.5.16/28`? | ✔ 10.0.5 | ✘ 40 is in 32–47 | outside |

**A block always starts where a chunk starts.** Chunks are cut evenly from 0,
so a /28 starts at a multiple of 16 and a /26 at 0, 64, 128 or 192.

- `10.0.5.16/28` is a real block, because 16 is a multiple of 16.
- `10.0.5.20/28` is **not** a block. 20 is in the middle of the 16–31 chunk.

**How many fit in a /24?** The number of chunks: 4 × /26, or 16 × /28. That is
how a /24 is split into small subnets.

### 7. The same trick, one number to the left (/17 to /23)

Between /16 and /24, the first **two** numbers are fixed, the **third** number
is cut into chunks, and the last number is a full `*`.

| Slash | Chunk size in the 3rd number | Addresses (chunk × 256) |
|---|---|---|
| /17 | 128 | 32,768 |
| /18 | 64 | 16,384 |
| /19 | 32 | 8,192 |
| /20 | **16** | 4,096 |
| /21 | 8 | 2,048 |
| /22 | 4 | 1,024 |
| /23 | 2 | 512 |

Example: `10.0.0.0/20`. The third number runs in a chunk of 16, so 0 to 15.
The block is `10.0.0.0` to `10.0.15.255`.

- `10.0.12.7`: first two match (10.0), third is 12, in 0–15. **Inside.**
- `10.0.20.7`: first two match, third is 20, not in 0–15. **Outside.** It is
  in the next chunk, `10.0.16.0/20`.

AWS's default VPC gives each AZ a /20 subnet like this one: 4,096 addresses.

### 8. Two blocks you will see everywhere

- **`0.0.0.0/0`**: zero numbers fixed, `*.*.*.*`. That is *every* address, in
  practice "the internet". A route `0.0.0.0/0 → internet gateway` means "send
  everything else to the internet".
- **`203.0.113.7/32`**: all four fixed, *exactly that one* address. A
  security-group rule "allow SSH from my IP" uses your address with `/32`.

### 9. Private addresses

Some ranges are for **internal use only**. The public internet cannot send
traffic to them.

| Range | Pattern |
|---|---|
| `10.0.0.0/8` | `10.*.*.*` |
| `172.16.0.0/12` | `172.16.*.*` to `172.31.*.*` |
| `192.168.0.0/16` | `192.168.*.*`, almost certainly your home Wi-Fi |

AWS networks use these. A machine with only a private address cannot be
reached from the internet. To be reachable it also needs a **public** address.

### 10. VPC and subnets: what AWS builds

- **VPC (Virtual Private Cloud).** Your own private network in AWS. You give it
  a block such as `10.0.0.0/16` (`10.0.*.*`, 65,536 addresses).
- **Subnet.** A smaller block inside the VPC's block. **Each subnet lives in
  exactly one Availability Zone.**

```
VPC  10.0.0.0/16  = 10.0.*.*   (65,536 addresses)
│
├── Subnet A  10.0.1.0/24 = 10.0.1.*  → AZ us-east-1a  (256)
├── Subnet B  10.0.2.0/24 = 10.0.2.*  → AZ us-east-1b  (256)
└── Subnet C  10.0.3.0/24 = 10.0.3.*  → AZ us-east-1c  (256)
```

Every subnet's pattern starts with `10.0`, so every subnet sits inside the VPC.
EC2 instances, databases and load balancers go into subnets and get an address
from the subnet's block. AWS allows VPCs and subnets from **/16 (biggest) to
/28 (smallest)**.

### 11. AWS keeps 5 addresses in every subnet

AWS takes the **first four and the last one** of every subnet. In
`10.0.1.0/24`:

| Address | Reserved for |
|---|---|
| `10.0.1.0` | network address: the subnet's own name |
| `10.0.1.1` | VPC router: the exit to other subnets |
| `10.0.1.2` | Amazon DNS: turns names into addresses |
| `10.0.1.3` | future use |
| `10.0.1.255` | broadcast. VPCs do not support it, but AWS still blocks it |

A /24 leaves 256 − 5 = **251 usable**. The same rule on a /28,
`10.0.5.16/28` (`.16` to `.31`):

```
.16  .17  .18  .19   .20 ... .30   .31
└── reserved (4) ──┘ └─ usable ─┘   └ reserved (last)
```

16 − 5 = **11 usable**. That is the exam's favourite: a /28 holds 11
instances, not 16. In general, **usable = block size − 5**.

Exam example: "You need 29 instances in one subnet. What is the smallest
CIDR?" A /27 has 32 addresses but only 27 usable, so it is too small. A
**/26** (59 usable) is the answer.

### 12. Let Python check you

```python
import ipaddress
ipaddress.ip_address("10.0.5.20") in ipaddress.ip_network("10.0.5.0/24")    # True
ipaddress.ip_address("10.0.5.130") in ipaddress.ip_network("10.0.5.64/26")  # False
net = ipaddress.ip_network("10.0.5.16/28")
net[0], net[-1], net.num_addresses                                           # .16, .31, 16
ipaddress.ip_network("10.0.5.20/28")   # ValueError: not the start of a chunk
```

## Numbers to know

| Fact | Value |
|---|---|
| One number in an address | 0–255 |
| Fixed numbers for /8 · /16 · /24 · /32 | 1 · 2 · 3 · 4 (slash ÷ 8) |
| Each +1 on the slash | halves the block |
| Addresses in /16 · /20 · /24 · /26 · /28 | 65,536 · 4,096 · 256 · 64 · 16 |
| VPC and subnet sizes | /16 (biggest) to /28 (smallest) |
| Reserved per subnet | 5: first four + last |
| Usable in a /24 · /26 · /28 | 251 · 59 · 11 |
| Private ranges | `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` |
| Everything · one address | `0.0.0.0/0` · `/32` |

## Exam traps

- **"/28 is bigger than /24."** Backwards. A bigger slash is a smaller block.
- **"A /28 holds 16 instances."** It holds 11. Always subtract the 5.
- **Rounding to the wrong size.** 29 instances need 34 addresses with the
  reserved five. That is a /26, not a /27.
- **"`0.0.0.0/0` means no addresses."** It means *all* of them.
- **"Allow SSH from my office IP" as `/24` or `/0`.** One address is `/32`.
  `/0` opens the port to the whole internet.
- **A block that starts mid-chunk.** `10.0.5.20/28` is not a block. A /28
  starts at a multiple of 16.
- **"A private address is reachable from the internet."** It is not. It also
  needs a public address and a route.
- **"A subnet spans two AZs."** Never. One subnet, one AZ.
- **Blocks bigger than /16 or smaller than /28.** AWS will not create them.

## Cost angle

- IP addresses inside your VPC (private ones) are **free**. So are VPCs and
  subnets.
- **Public IPv4 addresses cost** 0.005 USD per hour each, in use or idle (note
  05). Give public addresses only to what must face the internet.
- **Plan sizes once.** A subnet that is too small cannot be resized in place.
  Moving workloads to a new, bigger subnet costs time and risk. Week 02 shows
  how to plan.

## Self-check

Answer on paper first, then check with `ipaddress` in a Python shell.

1. Write `192.168.1.0/24` as a pattern with `*`. Is `192.168.1.77` inside? `192.168.2.77`?
2. Write `172.16.0.0/16` as a pattern. Is `172.16.200.5` inside? How many addresses does it hold?
3. What range does `10.0.5.128/26` cover? Is `10.0.5.200` inside it?
4. What range does `10.0.5.48/28` cover? Is `10.0.5.64` inside it?
5. Is `10.0.5.32/26` a real block?
6. Is `10.0.12.7` inside `10.0.0.0/20`? What about `10.0.20.7`?
7. How many usable IPs does AWS give you in `10.0.5.48/28`?
8. A security-group rule allows `0.0.0.0/0` on port 22. Who can try to connect?

Answers, cover them first:
1) `192.168.1.*`; yes (192, 168 and 1 match); no (third number is 2, not 1).
2) `172.16.*.*`; yes; 256 × 256 = 65,536.
3) `.128` to `.191` (128 + 64 − 1); no, 200 is past 191, in the next chunk.
4) `.48` to `.63` (48 + 16 − 1); no, 64 is the first address of the next chunk.
5) No. /26 blocks start only at 0, 64, 128 or 192.
6) Yes, the third number runs 0–15; no, 20 is outside it.
7) 16 − 5 = 11.
8) Anyone on the internet.

Now do drills 01 and 02 of week 02 when you reach that week: they make you build this address maths yourself. Today, the self-check above is enough.
