import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'TradingView Webhook',
  description: 'Receive and manage TradingView alerts',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
