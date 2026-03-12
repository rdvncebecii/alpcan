"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ViewerPage() {
  const orthancUrl =
    process.env.NEXT_PUBLIC_ORTHANC_URL || "http://localhost:8042";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">DICOM Viewer</h2>
        <p className="text-muted-foreground">
          OHIF Viewer ile DICOM görüntüleme
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Görüntüleyici</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="w-full h-[calc(100vh-250px)] bg-black rounded-lg flex items-center justify-center">
            <div className="text-center text-white/60">
              <p className="text-lg font-medium">OHIF Viewer</p>
              <p className="text-sm mt-2">
                DICOM görüntüleyici Orthanc bağlantısı kurulduğunda burada
                aktif olacaktır.
              </p>
              <p className="text-xs mt-4 text-white/40">
                Orthanc: {orthancUrl}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
