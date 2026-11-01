// Who is on screen in the intro and outro.
//
// Attribution notes, worth a glance before demo day:
//  * The QR codes were verified by decoding them. Ishan's is the file he supplied
//    (it resolves to his profile). Mahir's supplied image would not decode with two
//    separate readers, so his QR here is generated from the profile URL below and
//    was verified to scan.
//  * The headshots were paired by image size and upload order, which is a guess.
//    If the two faces are swapped, swap `photo` between the entries and nothing else.
export interface TeamMember {
  name: string;
  /** Job title, shown in bold under the name. */
  role: string;
  handle: string;
  url: string;
  photo: string;
  qr: string;
  /** Tailwind colour stops for the ring that spins behind the headshot. */
  ring: string;
}

export const TEAM: TeamMember[] = [
  {
    name: "Mahir Puri",
    role: "Software Engineer Intern at RBC (2x)",
    handle: "in/mahir-puri",
    url: "https://www.linkedin.com/in/mahir-puri/",
    photo: "/team/mahir.png",
    qr: "/team/mahir-qr.png",
    ring: "conic-gradient(from 0deg, #38bdf8, #a78bfa, #f472b6, #38bdf8)",
  },
  {
    name: "Ishan Sandhu",
    role: "Software Engineer at Fernwood Agentic",
    handle: "in/ishan-sandhu3121",
    url: "https://www.linkedin.com/in/ishan-sandhu3121/",
    photo: "/team/ishan.png",
    qr: "/team/ishan-qr.png",
    ring: "conic-gradient(from 0deg, #fbbf24, #34d399, #38bdf8, #fbbf24)",
  },
];
