import { describe, expect, it } from "vitest";

import { ApiError } from "./api-client";

describe("ApiError", () => {
  it("creates an error with status and message", () => {
    const error = new ApiError(404, "Not found");
    expect(error.name).toBe("ApiError");
    expect(error.status).toBe(404);
    expect(error.message).toBe("Not found");
  });
});
