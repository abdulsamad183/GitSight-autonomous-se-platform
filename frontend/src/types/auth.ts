export type User = {
  id: string;
  username: string;
  email: string;
  created_at: string;
};

export type RegisterInput = {
  username: string;
  email: string;
  password: string;
};

export type LoginInput = {
  email: string;
  password: string;
};
