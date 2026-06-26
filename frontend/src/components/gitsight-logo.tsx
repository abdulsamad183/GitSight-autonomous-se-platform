import Image from "next/image";
import Link from "next/link";

import { cn } from "@/lib/utils";

interface GitSightLogoProps {
  className?: string;
  height?: number;
  href?: string;
  priority?: boolean;
}

export function GitSightLogo({
  className,
  height = 40,
  href,
  priority = false,
}: GitSightLogoProps) {
  const image = (
    <Image
      src="/gitsight-logo.png"
      alt="GitSight"
      width={height}
      height={height}
      className={cn("object-contain", className)}
      style={{ height, width: "auto", maxWidth: "none" }}
      priority={priority}
    />
  );

  if (href) {
    return (
      <Link href={href} className="inline-flex shrink-0">
        {image}
      </Link>
    );
  }

  return image;
}
