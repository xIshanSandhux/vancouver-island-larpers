import { describe, expect, it } from "vitest";
import { API_URL } from "./api";

describe("template", () => {
  it("has an API url", () => {
    expect(API_URL).toMatch(/^https?:\/\//);
  });
});
