import { useEffect, useRef, useState } from "react";

export type BotanicalPosition =
  | "beside-left"
  | "beside-right"
  | "outer-top-right"
  | "outer-top-left"
  | "outer-bottom-left"
  | "outer-bottom-right"
  | "top-right"
  | "top-left"
  | "bottom-right"
  | "bottom-left"
  | "center-right"
  | "center-left"
  | "custom";

export type BotanicalVariant =
  | "side-sprig"
  | "side-bloom"
  | "flower-branch"
  | "blossom-sprig"
  | "flowering-stem"
  | "single"
  | "sprig"
  | "branch"
  | "vine"
  | "accent";

interface BotanicalLeafProps {
  position?: BotanicalPosition;
  className?: string;
  variant?: BotanicalVariant;
  style?: React.CSSProperties;
}

export function BotanicalLeaf({
  position = "beside-right",
  className = "",
  variant = "side-sprig",
  style,
}: BotanicalLeafProps) {
  const leafRef = useRef<HTMLDivElement>(null);
  const [isRevealed, setIsRevealed] = useState(false);

  useEffect(() => {
    const el = leafRef.current;
    if (!el) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setIsRevealed(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsRevealed(true);
          observer.unobserve(el);
        }
      },
      { threshold: 0.1, rootMargin: "0px 0px -20px 0px" }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={leafRef}
      className={`botanical-leaf-wrap botanical-${position} ${
        isRevealed ? "is-revealed" : ""
      } ${className}`}
      style={style}
      aria-hidden="true"
    >
      {variant === "side-sprig" ? (
        /* Arcs sideways beside cards: 3 sage leaves + 2 tiny ivory blossoms with yellow centers */
        <svg
          width="118"
          height="124"
          viewBox="0 0 118 124"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="botanical-svg"
        >
          {/* Main outward arching stem */}
          <path
            d="M10 114C24 94 48 76 72 48C84 34 96 22 108 14"
            stroke="#1b3d26"
            strokeWidth="1.3"
            strokeLinecap="round"
            opacity="0.75"
          />
          {/* Outward top leaf */}
          <path
            d="M108 14C114 26 112 38 100 44C88 50 82 40 84 30C86 22 98 16 108 14Z"
            fill="#beedc0"
            fillOpacity="0.65"
            stroke="#1b3d26"
            strokeWidth="1.15"
          />
          {/* Mid side leaf */}
          <path
            d="M68 54C82 46 94 50 96 60C98 70 86 76 76 72C68 68 64 60 68 54Z"
            fill="#cbeecb"
            fillOpacity="0.55"
            stroke="#1b3d26"
            strokeWidth="1.1"
          />
          {/* Lower trailing leaf */}
          <path
            d="M38 86C24 80 18 66 26 58C36 50 48 56 50 68C52 76 44 82 38 86Z"
            fill="#beedc0"
            fillOpacity="0.6"
            stroke="#1b3d26"
            strokeWidth="1.1"
          />
          {/* Vein lines */}
          <path
            d="M96 34C102 36 106 36 108 35M76 62C84 64 88 64 90 63M32 72C38 70 42 68 44 67"
            stroke="#1b3d26"
            strokeWidth="0.75"
            strokeLinecap="round"
            opacity="0.45"
          />
          {/* Tiny flower 1: Open ivory blossom beside stem */}
          <g transform="translate(94, 20)">
            <path d="M0 -6C2 -8 5 -5 3 -2C1 0 0 0 0 -6Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.75" />
            <path d="M6 -1C8 2 6 5 2 3C1 1 0 0 6 -1Z" fill="#fffdf6" stroke="#1b3d26" strokeWidth="0.75" />
            <path d="M3 5C1 7 -2 6 -2 4C-1 1 0 0 3 5Z" fill="#faf6eb" stroke="#1b3d26" strokeWidth="0.75" />
            <path d="M-5 3C-7 1 -6 -2 -4 -2C-2 -1 0 0 -5 3Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.75" />
            <circle cx="0" cy="0" r="1.8" fill="#fae69e" stroke="#1b3d26" strokeWidth="0.6" />
          </g>
          {/* Tiny flower 2: Subtle budding blossom */}
          <g transform="translate(56, 74)">
            <circle cx="0" cy="0" r="2.4" fill="#faf6eb" stroke="#1b3d26" strokeWidth="0.75" />
            <path d="M-1 -4C0 -5 2 -4 1 -2" stroke="#1b3d26" strokeWidth="0.6" />
            <circle cx="0" cy="0" r="1.1" fill="#edd69a" />
          </g>
        </svg>
      ) : variant === "side-bloom" ? (
        /* Designed to sit beside outer card edge: 2 leaves + 1 prominent ivory blossom + bud */
        <svg
          width="106"
          height="110"
          viewBox="0 0 106 110"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="botanical-svg"
        >
          {/* Stem */}
          <path
            d="M12 98C28 80 46 54 68 28C76 18 88 12 98 10"
            stroke="#1b3d26"
            strokeWidth="1.2"
            strokeLinecap="round"
            opacity="0.7"
          />
          {/* Lateral leaf */}
          <path
            d="M44 58C30 52 24 40 32 32C40 24 52 30 54 40C56 48 50 54 44 58Z"
            fill="#beedc0"
            fillOpacity="0.6"
            stroke="#1b3d26"
            strokeWidth="1.1"
          />
          {/* Upper leaf */}
          <path
            d="M66 32C78 24 90 28 92 36C94 44 84 50 76 46C70 42 66 36 66 32Z"
            fill="#d2f2d4"
            fillOpacity="0.5"
            stroke="#1b3d26"
            strokeWidth="1.05"
          />
          {/* Open ivory blossom */}
          <g transform="translate(86, 18)">
            <path d="M0 -7C3 -9 6 -6 4 -2C2 0 0 0 0 -7Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.8" />
            <path d="M7 -2C9 1 7 5 3 4C1 2 0 0 7 -2Z" fill="#fffdf6" stroke="#1b3d26" strokeWidth="0.8" />
            <path d="M4 6C2 9 -2 8 -2 5C-1 2 0 0 4 6Z" fill="#faf6eb" stroke="#1b3d26" strokeWidth="0.8" />
            <path d="M-6 4C-9 2 -8 -2 -5 -2C-2 -1 0 0 -6 4Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.8" />
            <path d="M-3 -6C-1 -9 3 -8 2 -5C1 -2 0 0 -3 -6Z" fill="#fffdf6" stroke="#1b3d26" strokeWidth="0.8" />
            <circle cx="0" cy="0" r="2.2" fill="#fae69e" stroke="#1b3d26" strokeWidth="0.7" />
          </g>
          {/* Secondary bud */}
          <circle cx="58" cy="46" r="2.5" fill="#faf6eb" stroke="#1b3d26" strokeWidth="0.7" />
          <circle cx="58" cy="46" r="1.1" fill="#edd69a" />
        </svg>
      ) : variant === "flower-branch" ? (
        /* Branch with leaves and two delicate ivory agricultural blossoms */
        <svg
          width="128"
          height="136"
          viewBox="0 0 128 136"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="botanical-svg"
        >
          <path
            d="M16 126C38 104 68 68 88 16"
            stroke="#1b3d26"
            strokeWidth="1.3"
            strokeLinecap="round"
            opacity="0.65"
          />
          <path
            d="M88 16C104 30 110 48 96 58C82 68 74 54 76 40C78 28 84 20 88 16Z"
            fill="#beedc0"
            fillOpacity="0.55"
            stroke="#1b3d26"
            strokeWidth="1.2"
          />
          <path
            d="M58 56C70 46 86 48 88 60C90 72 76 78 64 74C54 70 54 60 58 56Z"
            fill="#cbeecb"
            fillOpacity="0.45"
            stroke="#1b3d26"
            strokeWidth="1.1"
          />
          <path
            d="M40 88C24 80 18 64 28 56C38 48 50 56 52 68C54 78 46 84 40 88Z"
            fill="#beedc0"
            fillOpacity="0.5"
            stroke="#1b3d26"
            strokeWidth="1.1"
          />
          <path
            d="M84 42C90 46 98 46 101 45M42 66C34 64 28 60 26 57"
            stroke="#1b3d26"
            strokeWidth="0.75"
            strokeLinecap="round"
            opacity="0.45"
          />
          <g transform="translate(94, 28)">
            <path d="M0 -7C3 -9 6 -5 4 -2C2 0 0 0 0 -7Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.8" />
            <path d="M7 -2C9 1 7 5 3 4C1 2 0 0 7 -2Z" fill="#fffdf6" stroke="#1b3d26" strokeWidth="0.8" />
            <path d="M4 6C2 9 -2 8 -2 5C-1 2 0 0 4 6Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.8" />
            <path d="M-6 4C-9 2 -8 -2 -5 -2C-2 -1 0 0 -6 4Z" fill="#faf6eb" stroke="#1b3d26" strokeWidth="0.8" />
            <path d="M-3 -6C-1 -9 3 -8 2 -5C1 -2 0 0 -3 -6Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.8" />
            <circle cx="0" cy="0" r="2.2" fill="#fae69e" stroke="#1b3d26" strokeWidth="0.7" />
          </g>
          <g transform="translate(62, 78)">
            <path d="M0 -6C3 -8 5 -4 3 -1C1 1 0 0 0 -6Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.75" />
            <path d="M6 -1C8 2 6 5 2 3C1 1 0 0 6 -1Z" fill="#fffdf6" stroke="#1b3d26" strokeWidth="0.75" />
            <path d="M3 5C1 7 -2 6 -2 4C-1 1 0 0 3 5Z" fill="#faf6eb" stroke="#1b3d26" strokeWidth="0.75" />
            <path d="M-5 3C-7 1 -6 -2 -4 -2C-2 -1 0 0 -5 3Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.75" />
            <circle cx="0" cy="0" r="1.8" fill="#edd69a" stroke="#1b3d26" strokeWidth="0.6" />
          </g>
        </svg>
      ) : variant === "blossom-sprig" ? (
        /* Sprig with two sage leaves and an open ivory blossom */
        <svg
          width="104"
          height="112"
          viewBox="0 0 104 112"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="botanical-svg"
        >
          <path
            d="M18 100C36 82 56 56 74 20"
            stroke="#1b3d26"
            strokeWidth="1.2"
            strokeLinecap="round"
            opacity="0.6"
          />
          <path
            d="M74 20C88 32 92 48 80 56C68 64 60 52 62 40C64 30 70 22 74 20Z"
            fill="#beedc0"
            fillOpacity="0.5"
            stroke="#1b3d26"
            strokeWidth="1.1"
          />
          <path
            d="M50 56C34 50 26 38 34 30C42 22 54 30 56 40C58 48 54 52 50 56Z"
            fill="#d4f4d6"
            fillOpacity="0.45"
            stroke="#1b3d26"
            strokeWidth="1.1"
          />
          <path
            d="M70 42C76 46 82 46 84 45M46 42C40 38 34 36 32 34"
            stroke="#1b3d26"
            strokeWidth="0.7"
            strokeLinecap="round"
            opacity="0.4"
          />
          <g transform="translate(42, 28)">
            <path d="M0 -7C3 -9 5 -6 3 -2C2 0 0 0 0 -7Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.8" />
            <path d="M7 -2C9 1 6 5 2 3C1 1 0 0 7 -2Z" fill="#fffdf6" stroke="#1b3d26" strokeWidth="0.8" />
            <path d="M3 6C1 8 -3 7 -2 4C-1 1 0 0 3 6Z" fill="#faf6eb" stroke="#1b3d26" strokeWidth="0.8" />
            <path d="M-6 3C-8 1 -7 -3 -4 -2C-2 -1 0 0 -6 3Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.8" />
            <circle cx="0" cy="0" r="2" fill="#fae69e" stroke="#1b3d26" strokeWidth="0.7" />
          </g>
          <circle cx="78" cy="16" r="3" fill="#faf6eb" stroke="#1b3d26" strokeWidth="0.8" />
          <path d="M76 19C77 17 79 17 80 19" stroke="#1b3d26" strokeWidth="0.7" />
        </svg>
      ) : variant === "flowering-stem" ? (
        /* Curving stem with delicate leaves and nodding flower buds */
        <svg
          width="118"
          height="128"
          viewBox="0 0 118 128"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="botanical-svg"
        >
          <path
            d="M12 118C30 98 52 72 68 44C78 28 92 18 108 14"
            stroke="#1b3d26"
            strokeWidth="1.2"
            strokeLinecap="round"
            opacity="0.65"
          />
          <path
            d="M52 68C38 62 32 48 40 40C48 32 60 42 60 52C60 62 56 66 52 68Z"
            fill="#beedc0"
            fillOpacity="0.5"
            stroke="#1b3d26"
            strokeWidth="1.0"
          />
          <path
            d="M74 34C84 26 96 28 98 36C100 44 88 50 80 46C75 42 73 36 74 34Z"
            fill="#d2f2d4"
            fillOpacity="0.45"
            stroke="#1b3d26"
            strokeWidth="1.0"
          />
          <g transform="translate(104, 16)">
            <path d="M0 -6C2 -8 5 -5 3 -2C1 0 0 0 0 -6Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.75" />
            <path d="M6 -1C8 2 6 4 2 3C1 1 0 0 6 -1Z" fill="#fffdf6" stroke="#1b3d26" strokeWidth="0.75" />
            <path d="M3 5C1 7 -2 6 -2 3C-1 1 0 0 3 5Z" fill="#faf6eb" stroke="#1b3d26" strokeWidth="0.75" />
            <path d="M-5 2C-7 0 -6 -3 -3 -2C-1 -1 0 0 -5 2Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.75" />
            <circle cx="0" cy="0" r="1.8" fill="#edd69a" stroke="#1b3d26" strokeWidth="0.6" />
          </g>
          <g transform="translate(68, 44)">
            <circle cx="0" cy="0" r="2.4" fill="#faf6eb" stroke="#1b3d26" strokeWidth="0.75" />
            <path d="M-1 -4C0 -5 2 -4 1 -2" stroke="#1b3d26" strokeWidth="0.6" />
            <circle cx="0" cy="0" r="1.1" fill="#fae69e" />
          </g>
        </svg>
      ) : variant === "single" ? (
        <svg
          width="74"
          height="88"
          viewBox="0 0 74 88"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="botanical-svg"
        >
          <path
            d="M12 82C24 64 38 42 48 10"
            stroke="#1b3d26"
            strokeWidth="1.2"
            strokeLinecap="round"
            opacity="0.6"
          />
          <path
            d="M48 10C62 26 66 48 46 64C28 78 22 62 26 44C30 26 40 14 48 10Z"
            fill="#beedc0"
            fillOpacity="0.45"
            stroke="#1b3d26"
            strokeWidth="1.2"
            strokeLinejoin="round"
          />
          <path
            d="M38 52C44 48 52 46 56 47M32 38C38 34 46 32 50 33M42 24C46 20 50 18 52 18"
            stroke="#1b3d26"
            strokeWidth="0.8"
            strokeLinecap="round"
            opacity="0.5"
          />
        </svg>
      ) : variant === "branch" ? (
        <svg
          width="112"
          height="124"
          viewBox="0 0 112 124"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="botanical-svg"
        >
          <path
            d="M14 116C36 94 62 62 82 14"
            stroke="#1b3d26"
            strokeWidth="1.3"
            strokeLinecap="round"
            opacity="0.65"
          />
          <path
            d="M82 14C98 28 104 46 90 56C76 66 68 52 70 38C72 26 78 18 82 14Z"
            fill="#beedc0"
            fillOpacity="0.55"
            stroke="#1b3d26"
            strokeWidth="1.2"
          />
          <path
            d="M58 52C70 42 86 44 88 56C90 68 76 74 64 70C54 66 54 56 58 52Z"
            fill="#cbeecb"
            fillOpacity="0.4"
            stroke="#1b3d26"
            strokeWidth="1.1"
          />
          <path
            d="M38 82C22 74 16 58 26 50C36 42 48 50 50 62C52 72 44 78 38 82Z"
            fill="#beedc0"
            fillOpacity="0.5"
            stroke="#1b3d26"
            strokeWidth="1.1"
          />
          <path
            d="M78 40C84 44 92 44 95 43M74 30C80 32 86 32 89 31M40 60C32 58 26 54 24 51"
            stroke="#1b3d26"
            strokeWidth="0.8"
            strokeLinecap="round"
            opacity="0.45"
          />
        </svg>
      ) : variant === "vine" ? (
        <svg
          width="130"
          height="140"
          viewBox="0 0 130 140"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="botanical-svg"
        >
          <path
            d="M10 130C30 110 50 80 65 50C75 30 90 18 115 12"
            stroke="#1b3d26"
            strokeWidth="1.3"
            strokeLinecap="round"
            opacity="0.65"
          />
          <path
            d="M115 12C126 20 128 32 118 40C108 48 98 38 102 28C104 20 110 14 115 12Z"
            fill="#beedc0"
            fillOpacity="0.5"
            stroke="#1b3d26"
            strokeWidth="1.1"
          />
          <path
            d="M75 36C86 28 98 30 100 38C102 46 90 52 82 48C76 44 74 38 75 36Z"
            fill="#d2f2d4"
            fillOpacity="0.45"
            stroke="#1b3d26"
            strokeWidth="1.0"
          />
          <path
            d="M50 75C34 68 28 54 36 46C46 38 58 48 58 58C58 68 54 72 50 75Z"
            fill="#beedc0"
            fillOpacity="0.55"
            stroke="#1b3d26"
            strokeWidth="1.1"
          />
          <path
            d="M32 105C48 98 56 102 58 110C60 118 48 124 38 120C32 116 30 108 32 105Z"
            fill="#cbeecb"
            fillOpacity="0.4"
            stroke="#1b3d26"
            strokeWidth="1.0"
          />
          <path
            d="M48 60C42 56 36 52 34 50M110 28C116 30 122 30 124 29"
            stroke="#1b3d26"
            strokeWidth="0.75"
            strokeLinecap="round"
            opacity="0.4"
          />
        </svg>
      ) : variant === "accent" ? (
        <svg
          width="68"
          height="72"
          viewBox="0 0 68 72"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="botanical-svg"
        >
          <path
            d="M8 64C22 50 36 32 54 12"
            stroke="#1b3d26"
            strokeWidth="1.1"
            strokeLinecap="round"
            opacity="0.6"
          />
          <path
            d="M54 12C64 22 66 34 56 42C46 50 38 40 42 28C44 20 50 14 54 12Z"
            fill="#beedc0"
            fillOpacity="0.45"
            stroke="#1b3d26"
            strokeWidth="1.1"
          />
          <path
            d="M34 40C22 36 16 26 24 20C32 14 40 22 40 30C40 36 36 38 34 40Z"
            fill="#d2f2d4"
            fillOpacity="0.4"
            stroke="#1b3d26"
            strokeWidth="1.0"
          />
          <path
            d="M48 28C54 32 58 32 60 31"
            stroke="#1b3d26"
            strokeWidth="0.75"
            strokeLinecap="round"
            opacity="0.4"
          />
        </svg>
      ) : (
        /* Sprig (default) */
        <svg
          width="96"
          height="102"
          viewBox="0 0 96 102"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="botanical-svg"
        >
          <path
            d="M16 92C34 76 54 50 72 16"
            stroke="#1b3d26"
            strokeWidth="1.2"
            strokeLinecap="round"
            opacity="0.6"
          />
          <path
            d="M72 16C86 28 90 44 78 52C66 60 58 48 60 36C62 26 68 18 72 16Z"
            fill="#beedc0"
            fillOpacity="0.5"
            stroke="#1b3d26"
            strokeWidth="1.2"
          />
          <path
            d="M48 52C32 46 24 34 32 26C40 18 52 26 54 36C56 44 52 48 48 52Z"
            fill="#d4f4d6"
            fillOpacity="0.45"
            stroke="#1b3d26"
            strokeWidth="1.1"
          />
          <path
            d="M58 40C68 34 76 38 78 46C80 52 72 56 64 54C58 52 56 44 58 40Z"
            fill="#beedc0"
            fillOpacity="0.4"
            stroke="#1b3d26"
            strokeWidth="1.0"
          />
          <path
            d="M68 38C74 42 80 42 82 41M44 38C38 34 32 32 30 30"
            stroke="#1b3d26"
            strokeWidth="0.75"
            strokeLinecap="round"
            opacity="0.4"
          />
        </svg>
      )}
    </div>
  );
}
