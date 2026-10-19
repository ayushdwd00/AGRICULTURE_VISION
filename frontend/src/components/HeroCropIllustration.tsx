import { useEffect, useRef, useState } from "react";
import { Sprout, Check } from "lucide-react";

export function HeroCropIllustration() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isRevealed, setIsRevealed] = useState(false);

  useEffect(() => {
    const el = containerRef.current;
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
      { threshold: 0.1 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={containerRef}
      className={`hero-crop-stage ${isRevealed ? "is-revealed" : ""}`}
      aria-hidden="true"
    >
      {/* Decorative botanical halo */}
      <div className="crop-halo" />

      {/* Main Botanical Crop Artwork */}
      <svg
        className="crop-svg"
        viewBox="0 0 460 480"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="stemGrad" x1="230" y1="420" x2="230" y2="70" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#1b3d26" stopOpacity="0.8" />
            <stop offset="60%" stopColor="#2c5f3b" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#4a855b" stopOpacity="0.6" />
          </linearGradient>
          <linearGradient id="leafGrad1" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#beedc0" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#9fd6a3" stopOpacity="0.65" />
          </linearGradient>
          <linearGradient id="leafGrad2" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#d2f2d4" stopOpacity="0.85" />
            <stop offset="100%" stopColor="#b4e4b7" stopOpacity="0.55" />
          </linearGradient>
          <linearGradient id="soilGrad" x1="160" y1="435" x2="300" y2="435" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#786c5e" stopOpacity="0.1" />
            <stop offset="50%" stopColor="#5c4d3c" stopOpacity="0.32" />
            <stop offset="100%" stopColor="#786c5e" stopOpacity="0.1" />
          </linearGradient>
        </defs>

        {/* Soil mound & growing base */}
        <ellipse cx="230" cy="442" rx="100" ry="14" fill="url(#soilGrad)" />
        <path
          d="M170 442C190 436 270 436 290 442"
          stroke="#1b3d26"
          strokeWidth="1.2"
          strokeLinecap="round"
          strokeDasharray="4 4"
          opacity="0.4"
        />

        {/* Subtle Root tendrils */}
        <path
          d="M230 438C222 452 210 460 200 465M230 438C236 454 246 462 258 466M228 440C226 448 222 455 218 458"
          stroke="#1b3d26"
          strokeWidth="1"
          strokeLinecap="round"
          opacity="0.35"
        />

        {/* Central Plant Stem */}
        <path
          d="M230 438C228 360 236 260 226 150C222 108 228 78 230 65"
          stroke="url(#stemGrad)"
          strokeWidth="3.2"
          strokeLinecap="round"
        />

        {/* Branch 1 - Lower Left Mature Leaf */}
        <path
          d="M229 365C198 355 160 368 120 380"
          stroke="#1b3d26"
          strokeWidth="1.8"
          strokeLinecap="round"
          opacity="0.7"
        />
        <path
          d="M120 380C100 348 112 308 148 300C182 292 208 322 229 365Z"
          fill="url(#leafGrad1)"
          stroke="#1b3d26"
          strokeWidth="1.4"
          strokeLinejoin="round"
        />
        {/* Veins for Leaf 1 */}
        <path
          d="M124 376C148 348 174 326 218 348"
          stroke="#1b3d26"
          strokeWidth="1"
          strokeLinecap="round"
          opacity="0.5"
        />
        <path
          d="M148 348C140 334 136 322 138 312M172 338C168 324 166 312 168 306M192 344C190 332 192 322 196 316"
          stroke="#1b3d26"
          strokeWidth="0.8"
          strokeLinecap="round"
          opacity="0.45"
        />

        {/* Branch 2 - Lower Right Leaf */}
        <path
          d="M230 335C268 328 310 338 348 352"
          stroke="#1b3d26"
          strokeWidth="1.8"
          strokeLinecap="round"
          opacity="0.7"
        />
        <path
          d="M348 352C364 316 348 276 314 270C276 264 252 295 230 335Z"
          fill="url(#leafGrad2)"
          stroke="#1b3d26"
          strokeWidth="1.4"
          strokeLinejoin="round"
        />
        {/* Veins for Leaf 2 */}
        <path
          d="M344 348C318 318 290 298 244 316"
          stroke="#1b3d26"
          strokeWidth="1"
          strokeLinecap="round"
          opacity="0.5"
        />
        <path
          d="M318 318C324 302 328 292 326 282M292 306C296 292 298 282 296 274M268 312C270 300 270 292 268 286"
          stroke="#1b3d26"
          strokeWidth="0.8"
          strokeLinecap="round"
          opacity="0.45"
        />

        {/* Branch 3 - Mid Left Leaf */}
        <path
          d="M228 260C190 242 152 238 108 246"
          stroke="#1b3d26"
          strokeWidth="1.6"
          strokeLinecap="round"
          opacity="0.75"
        />
        <path
          d="M108 246C96 210 114 175 146 170C180 165 204 198 228 260Z"
          fill="url(#leafGrad1)"
          stroke="#1b3d26"
          strokeWidth="1.4"
          strokeLinejoin="round"
        />
        {/* Veins for Leaf 3 */}
        <path
          d="M112 242C140 216 168 200 214 228"
          stroke="#1b3d26"
          strokeWidth="0.9"
          strokeLinecap="round"
          opacity="0.5"
        />
        <path
          d="M140 216C134 202 130 190 134 182M164 208C160 194 158 184 162 178M188 214C186 202 188 194 192 188"
          stroke="#1b3d26"
          strokeWidth="0.75"
          strokeLinecap="round"
          opacity="0.45"
        />

        {/* Branch 4 - Mid Right Upward Leaf */}
        <path
          d="M227 210C260 185 304 176 345 180"
          stroke="#1b3d26"
          strokeWidth="1.6"
          strokeLinecap="round"
          opacity="0.75"
        />
        <path
          d="M345 180C352 142 330 112 296 114C260 116 242 150 227 210Z"
          fill="url(#leafGrad2)"
          stroke="#1b3d26"
          strokeWidth="1.4"
          strokeLinejoin="round"
        />
        {/* Veins for Leaf 4 */}
        <path
          d="M338 178C308 152 278 140 236 174"
          stroke="#1b3d26"
          strokeWidth="0.9"
          strokeLinecap="round"
          opacity="0.5"
        />
        <path
          d="M306 150C310 136 312 126 308 120M278 142C280 130 280 122 278 118"
          stroke="#1b3d26"
          strokeWidth="0.75"
          strokeLinecap="round"
          opacity="0.45"
        />

        {/* Branch 5 - Upper Left Young Leaf */}
        <path
          d="M226 150C198 128 170 116 138 114"
          stroke="#1b3d26"
          strokeWidth="1.4"
          strokeLinecap="round"
          opacity="0.7"
        />
        <path
          d="M138 114C134 84 154 62 178 62C204 62 216 94 226 150Z"
          fill="url(#leafGrad1)"
          stroke="#1b3d26"
          strokeWidth="1.3"
          strokeLinejoin="round"
        />
        <path
          d="M142 112C162 92 184 82 216 112"
          stroke="#1b3d26"
          strokeWidth="0.8"
          strokeLinecap="round"
          opacity="0.5"
        />

        {/* Branch 6 - Top Shoot Leaf (Crown) */}
        <path
          d="M230 65C232 40 248 24 258 20C264 36 256 56 230 65Z"
          fill="url(#leafGrad2)"
          stroke="#1b3d26"
          strokeWidth="1.2"
          strokeLinejoin="round"
        />
        <path
          d="M230 65C222 45 212 32 202 30C202 46 214 58 230 65Z"
          fill="url(#leafGrad1)"
          stroke="#1b3d26"
          strokeWidth="1.2"
          strokeLinejoin="round"
        />

        {/* Small Botanical Buds & Nodes */}
        <circle cx="227" cy="210" r="3" fill="#beedc0" stroke="#1b3d26" strokeWidth="1" />
        <circle cx="228" cy="260" r="3" fill="#beedc0" stroke="#1b3d26" strokeWidth="1" />
        <circle cx="229" cy="365" r="3" fill="#beedc0" stroke="#1b3d26" strokeWidth="1" />

        {/* Agricultural Blossoms & Flowers */}
        {/* Blossom 1 - Mid-upper flowering bloom */}
        <g transform="translate(236, 175)">
          <path d="M0 -9C4 -11 8 -6 5 -2C3 1 0 0 0 -9Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.85" />
          <path d="M9 -2C11 2 8 7 3 5C1 3 0 0 9 -2Z" fill="#fffdf6" stroke="#1b3d26" strokeWidth="0.85" />
          <path d="M5 8C2 11 -3 10 -3 6C-1 3 0 0 5 8Z" fill="#faf6eb" stroke="#1b3d26" strokeWidth="0.85" />
          <path d="M-8 4C-11 2 -9 -3 -5 -2C-2 -1 0 0 -8 4Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.85" />
          <path d="M-4 -8C-1 -11 4 -10 3 -6C1 -3 0 0 -4 -8Z" fill="#fffdf6" stroke="#1b3d26" strokeWidth="0.85" />
          <circle cx="0" cy="0" r="2.8" fill="#fae69e" stroke="#1b3d26" strokeWidth="0.75" />
        </g>

        {/* Blossom 2 - Lower branch flowering bud */}
        <g transform="translate(215, 320)">
          <path d="M0 -7C3 -9 6 -5 4 -2C2 0 0 0 0 -7Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.8" />
          <path d="M7 -2C9 1 6 5 2 3C1 1 0 0 7 -2Z" fill="#fffdf6" stroke="#1b3d26" strokeWidth="0.8" />
          <path d="M3 6C1 8 -3 7 -2 4C-1 1 0 0 3 6Z" fill="#faf6eb" stroke="#1b3d26" strokeWidth="0.8" />
          <path d="M-6 3C-8 1 -7 -3 -4 -2C-2 -1 0 0 -6 3Z" fill="#fffff3" stroke="#1b3d26" strokeWidth="0.8" />
          <circle cx="0" cy="0" r="2.2" fill="#edd69a" stroke="#1b3d26" strokeWidth="0.7" />
        </g>

        {/* Blossom 3 - Upper crown bud */}
        <g transform="translate(244, 90)">
          <circle cx="0" cy="0" r="3.2" fill="#faf6eb" stroke="#1b3d26" strokeWidth="0.8" />
          <path d="M-1 -5C0 -6 2 -5 1 -3" stroke="#1b3d26" strokeWidth="0.7" />
          <circle cx="0" cy="0" r="1.3" fill="#fae69e" />
        </g>
      </svg>

      {/* Floating Organic Botanical Badges */}
      <div className="crop-badge crop-badge-top">
        <span className="crop-badge-icon">
          <Check size={11} strokeWidth={3} />
        </span>
        <span className="crop-badge-text">Botanical Model · Illustrative Guide</span>
      </div>

      <div className="crop-badge crop-badge-bottom">
        <span className="crop-badge-icon">
          <Sprout size={12} />
        </span>
        <span className="crop-badge-text">Canopy Architecture · Optical Guidance</span>
      </div>
    </div>
  );
}
