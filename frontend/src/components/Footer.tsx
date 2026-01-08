'use client';

import Link from 'next/link';
import Image from 'next/image';
import { Mail, Phone, Globe } from 'lucide-react';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="relative z-10 bg-gradient-to-r from-slate-800 via-blue-900 to-slate-800 text-white border-t border-blue-700/30">
      <div className="container mx-auto px-16 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-20">
          {/* Company Info */}
          <div>
            <Link href="/">
              <Image
                src="/assets/slt-mobitel-logo.png"
                alt="SLT-MOBITEL"
                width={150}
                height={50}
                className="mb-4 hover:scale-105 transition-transform duration-300 cursor-pointer"
                priority
              />
            </Link>
            <p className="text-blue-100 text-sm leading-relaxed">
              Professional office DBMS assistant powered by AI-MCP 
              for enhanced daily operations plus effcient work for employers.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-blue-400 text-lg font-normal mb-4">Quick Links</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/" className="text-blue-100 hover:text-white transition-colors">
                  Home
                </Link>
              </li>
              <li>
                <Link href="/instructions" className="text-blue-100 hover:text-white transition-colors">
                  Instructions
                </Link>
              </li>
              <li>
                <a href="#" className="text-blue-100 hover:text-white transition-colors">
                  Support
                </a>
              </li>
            </ul>
          </div>

          {/* Contact Info */}
          <div>
            <h3 className="text-blue-400 text-lg font-normal mb-4">Contact</h3>
            <div className="space-y-2 text-sm text-blue-100">
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4" />
                <a href="tel:+94112021000" className="text-blue-100 hover:text-white transition-colors">
                  +94 112 021 000
                </a>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4" />
                <a href="mailto:support@slt.lk" className="text-blue-100 hover:text-white transition-colors">
                  support@slt.lk
                </a>
              </div>
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4" />
                <a href="https://www.slt.lk" className="text-blue-100 hover:text-white transition-colors">
                  www.slt.lk
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="text-blue-400 mt-8 pt-6 border-t border-blue-700/30 flex flex-col md:flex-row justify-between items-center text-sm text-blue-100">
          <p>
            © {currentYear} SLT-MOBITEL™. <span className='text-blue-100'> ® All Rights Reserved.</span>
          </p>
          <div className="flex gap-6 mt-4 md:mt-0">
            <a href="#" className="hover:text-white transition-colors">
              Privacy Policy
            </a>
            <a href="#" className="hover:text-white transition-colors">
              Terms of Service
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}