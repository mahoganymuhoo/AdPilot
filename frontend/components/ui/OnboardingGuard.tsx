"use client";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

export default function OnboardingGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (pathname === "/onboarding") {
      setChecked(true);
      return;
    }
    const done = localStorage.getItem("adpilot_onboarded");
    if (!done) {
      router.replace("/onboarding");
    } else {
      setChecked(true);
    }
  }, [pathname]);

  if (!checked && pathname !== "/onboarding") return null;
  return <>{children}</>;
}
