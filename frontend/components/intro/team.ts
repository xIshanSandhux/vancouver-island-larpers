// Who is on screen in the intro and outro.
//
// The headshots were paired by image size and upload order. If the two faces are
// swapped, swap `photo` between the entries and nothing else.
export interface TeamMember {
  name: string;
  /** Job title, shown in bold under the name. */
  role: string;
  photo: string;
  /** Tailwind colour stops for the ring that spins behind the headshot. */
  ring: string;
}

export const TEAM: TeamMember[] = [
  {
    name: "Mahir Puri",
    role: "Workflow and product builder",
    photo: "/team/mahir.png",
    ring: "conic-gradient(from 0deg, #38bdf8, #a78bfa, #f472b6, #38bdf8)",
  },
  {
    name: "Ishan Sandhu",
    role: "Audience and experience builder",
    photo: "/team/ishan.png",
    ring: "conic-gradient(from 0deg, #fbbf24, #34d399, #38bdf8, #fbbf24)",
  },
];
