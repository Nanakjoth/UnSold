/**
 * Pure, side-effect-free maths for the NeuralBackdrop canvas.
 * No DOM access — testable in any JS runtime.
 */

export type Vec3 = { x: number; y: number; z: number };
export type Edge = [number, number];
export type Graph = { points: Vec3[]; edges: Edge[] };
export type ProjectedPoint = { x: number; y: number; s: number; z: number };
export type ProjectParams = {
  angleY: number; // rotation around the vertical axis (radians)
  tiltX: number; // rotation around the horizontal axis (radians)
  focal: number; // perspective distance; larger = flatter
  radius: number; // scene radius in pixels
  originX: number; // canvas-space centre
  originY: number;
};

/** Deterministic PRNG (mulberry32) so the layout is stable per mount. */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Node 0 sits at the origin ("you"); the other n-1 points are sampled inside
 * the unit sphere. Each node links to its 3 nearest neighbours (node 0 to 4),
 * deduplicated as undirected pairs. Distances are rotation-invariant, so the
 * links never need rebuilding under rotation.
 */
export function buildGraph(n: number, rng: () => number): Graph {
  const count = Math.max(2, Math.floor(n));
  const points: Vec3[] = [{ x: 0, y: 0, z: 0 }];
  while (points.length < count) {
    const x = rng() * 2 - 1;
    const y = rng() * 2 - 1;
    const z = rng() * 2 - 1;
    if (x * x + y * y + z * z <= 1) points.push({ x, y, z });
  }
  const edges: Edge[] = [];
  const seen = new Set<string>();
  for (let i = 0; i < count; i++) {
    const near = points
      .map((p, j) => ({
        j,
        d: (p.x - points[i].x) ** 2 + (p.y - points[i].y) ** 2 + (p.z - points[i].z) ** 2,
      }))
      .filter((o) => o.j !== i)
      .sort((a, b) => a.d - b.d)
      .slice(0, i === 0 ? 4 : 3);
    for (const { j } of near) {
      const a = Math.min(i, j);
      const b = Math.max(i, j);
      const key = `${a}-${b}`;
      if (!seen.has(key)) {
        seen.add(key);
        edges.push([a, b]);
      }
    }
  }
  return { points, edges };
}

/** Rotate around Y then X, then perspective-project. Larger z = farther away. */
export function projectPoints(points: readonly Vec3[], params: ProjectParams): ProjectedPoint[] {
  const { angleY, tiltX, focal, radius, originX, originY } = params;
  const cosY = Math.cos(angleY);
  const sinY = Math.sin(angleY);
  const cosX = Math.cos(tiltX);
  const sinX = Math.sin(tiltX);
  const f = focal > 0 ? focal : 1;
  return points.map((p) => {
    const x1 = p.x * cosY + p.z * sinY;
    const z1 = -p.x * sinY + p.z * cosY;
    const y2 = p.y * cosX - z1 * sinX;
    const z2 = p.y * sinX + z1 * cosX;
    const s = f / (f + z2);
    return { x: originX + x1 * radius * s, y: originY + y2 * radius * s, s, z: z2 };
  });
}

/** Nearness in 0..1: 1 = nearest (z = -1), 0 = farthest (z = +1). */
export function depthOf(z: number): number {
  return 1 - (z + 1) / 2;
}
